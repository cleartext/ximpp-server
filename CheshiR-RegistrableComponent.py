#!bin/python

import logging
from SimpleBackend import SimpleBackend
from HTTPFrontend import HTTPFrontend
from RegistrableComponent import RegistrableComponent

# Uncomment the following line to turn on debugging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

def main() :
	backend = SimpleBackend()
	backend.jidToUser = {
        'user1@coolbananas.com.au': 'peter',
        'user2@coolbananas.com.au': 'kevin',
    }
	backend.userToJID = {
        'peter' : 'user1@coolbananas.com.au',
        'kevin' : 'user2@coolbananas.com.au'
      }
	component = RegistrableComponent(
		jid = "microblog.coolbananas.com.au", password = "cleartext7u$",
		server = "xmpp1.cleartext.im", port = 5349, backend = backend)
	component.start()
	httpFrontend = HTTPFrontend(8080, backend)
	httpFrontend.start()

if __name__ == '__main__' :
	main()
