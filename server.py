#!bin/python

import signal
import logging
import yaml

from frontend import HTTPFrontend
from bot import Bot
from pdb import set_trace

import db

def init(cfg):
    # Init logging
    logging.basicConfig(
        level = logging.DEBUG,
        format = '%(levelname)-8s %(name)-8s %(message)s'
    )
    root = logging.getLogger()
    handler = logging.FileHandler('debug.log')
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
