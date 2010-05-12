#!bin/python

import logging
from backend.simple import Backend
from frontend import HTTPFrontend
from bot import Bot

# Uncomment the following line to turn on debugging
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(levelname)-8s %(message)s'
)


def main():
    backend = Backend()
    backend.jidToUser = {
        'user1@coolbananas.com.au': 'peter',
        'user2@coolbananas.com.au': 'kevin',
    }
    backend.userToJID = {
        'peter': 'user1@coolbananas.com.au',
        'kevin': 'user2@coolbananas.com.au'
      }
    component = Bot(
        jid = "microblog.coolbananas.com.au", password = "cleartext7u$",
        server = "xmpp1.cleartext.im", port = 5349, backend = backend)
    component.start()
    httpFrontend = HTTPFrontend(8080, backend)
    httpFrontend.start()


if __name__ == '__main__':
    main()
