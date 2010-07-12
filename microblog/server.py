#!bin/python

import logging
import signal
import sys
import yaml

from microblog import db
from microblog.bot import Bot

from pdb import set_trace

import traceback, signal, threading


def dumpstacks(signal, frame):
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name[threadId], threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    print "\n".join(code)


def debug(sig, frame):
    set_trace()


def init(cfg):
    if cfg['component'].get('debug', False):
        signal.signal(signal.SIGUSR1, debug)

    # Init logging
    lcfg = cfg.get('logging', {})
    level = getattr(
        logging,
        lcfg.get('level', 'ERROR').upper()
    )
    filename = lcfg.get('filename', 'debug.log')

    logging.basicConfig(
        level = level,
        format = '%(levelname)-8s %(name)-8s %(filename)s:%(lineno)s %(message)s'
    )
    root = logging.getLogger()
    handler = logging.FileHandler(filename)
    fmt =  logging.Formatter('%(asctime)s %(process)s/%(thread)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s')
    handler.setFormatter(fmt)
    root.addHandler(handler)

    # Init database
    db.init(cfg['database'])


def start_bot():
    if len(sys.argv) != 2:
        print 'Usage: %s config.cfg' % sys.argv[0]
        sys.exit(1)

    cfg = yaml.load(open(sys.argv[1]).read())

    init(cfg)
    bot = Bot(**cfg['component'])

    bot.start()



def start_frontend():
    from microblog.frontend import Frontend

    if len(sys.argv) != 2:
        print 'Usage: %s config.cfg' % sys.argv[0]
        sys.exit(1)

    cfg = yaml.load(open(sys.argv[1]).read())

    init(cfg)

    cfg['frontend']['login_url'] = '/login/'
    Frontend(**cfg['frontend']).start()


if __name__ == '__main__':
    start_bot()
