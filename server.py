#!bin/python

import logging
from backend.simple import Backend
from frontend import HTTPFrontend
from bot import Bot

import db

# Uncomment the following line to turn on debugging
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(levelname)-8s %(message)s'
)


def main():
    db.init('mysql://root:cleartext.netgeDiM76A5@localhost/coolbananas_com_au')

    backend = Backend(domain = 'coolbananas.com.au')
#k    backend.jidToUser = {
#k        'user1@coolbananas.com.au': 'peter',
#k        'user2@coolbananas.com.au': 'kevin',
#k    }
#k    backend.userToJID = {
#k        'peter': 'user1@coolbananas.com.au',
#k        'kevin': 'user2@coolbananas.com.au'
#k      }
    component = Bot(
        jid = "microblog.coolbananas.com.au", password = "cleartext7u$",
        server = "xmpp1.cleartext.im", port = 5349, backend = backend)
    component.start()
    httpFrontend = HTTPFrontend(8080, backend)
    httpFrontend.start()


if __name__ == '__main__':
    main()
