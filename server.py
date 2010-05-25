#!bin/python

import signal
import logging
import yaml

from backend.simple import Backend
from frontend import HTTPFrontend
from bot import Bot
from pdb import set_trace

import db

# Uncomment the following line to turn on debugging
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(levelname)-8s %(message)s'
)
root = logging.getLogger()
handler = logging.FileHandler('debug.log')
fmt =  logging.Formatter('%(asctime)s %(process)s/%(thread)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s')
handler.setFormatter(fmt)
root.addHandler(handler)

def init(cfg):
    db.init('mysql://%(username)s:%(password)s@%(host)s/%(dbname)s' % cfg['database'])



def main():
    if len(sys.argv) != 2:
        print 'Usage: %s config.cfg' % sys.argv[0]
        sys.exit(1)

    cfg = yaml.load(open(sys.argv[1]).read())

    init(cfg)
    backend = Backend(domain = 'coolbananas.com.au')
    bot = Bot(backend = backend, **cfg['component'])

    bot.start()

    # does not work, because bot running in single threaded mode.
    #frontend = HTTPFrontend(8080, backend)
    #frontend.start()


if __name__ == '__main__':
    main()
