#!bin/python

import logging
import signal
import sys
import yaml

from microblog import db
from microblog.bot import Bot
from microblog.frontend import HTTPFrontend

from pdb import set_trace


def init(cfg):
    # Init logging
    lcfg = cfg.get('logging', {})
    level = getattr(
        logging,
        lcfg.get('level', 'ERROR').upper()
    )
    filename = lcfg.get('filename', 'debug.log')

    logging.basicConfig(
        level = level,
        format = '%(levelname)-8s %(name)-8s %(message)s'
    )
    root = logging.getLogger()
    handler = logging.FileHandler(filename)
    fmt =  logging.Formatter('%(asctime)s %(process)s/%(thread)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s')
    handler.setFormatter(fmt)
    root.addHandler(handler)

    # Init database
    db.init(cfg['database'])


def main():
    if len(sys.argv) != 2:
        print 'Usage: %s config.cfg' % sys.argv[0]
        sys.exit(1)

    cfg = yaml.load(open(sys.argv[1]).read())

    init(cfg)
    bot = Bot(**cfg['component'])

    bot.start()

    # does not work, because bot running in single threaded mode.
    #frontend = HTTPFrontend(8080)
    #frontend.start()


if __name__ == '__main__':
    main()
