#!bin/python

import signal
import logging
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

def init():
    db.init('mysql://root:cleartext.netgeDiM76A5@localhost/coolbananas_com_au')



def main():
    init()
    backend = Backend(domain = 'coolbananas.com.au')
    bot = Bot(
        jid = "microblog.coolbananas.com.au", password = "cleartext7u$",
        server = "xmpp1.cleartext.im", port = 5349, backend = backend)

    bot.start()

    # does not work, because bot running in single threaded mode.
    #frontend = HTTPFrontend(8080, backend)
    #frontend.start()


if __name__ == '__main__':
    main()
