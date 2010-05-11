#!/usr/bin/env python

import logging
#from SimpleBackend import SimpleBackend
from RMQBackend import RMQBackend
from HTTPFrontend import HTTPFrontend
from Bot import Bot

# Uncomment the following line to turn on debugging
#logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

def main() :
	#backend = SimpleBackend()
	#bot = Bot("bot@cheshir.lit", "mypass", backend, "http://cheshir.lit")
	backend = RMQBackend('palala.org', 'guest', 'JfMxYJnb9zc4vHmBBXJp')
	bot = Bot('test@code-bear.com', 'jasmine42', backend, 'http://localhost')
	bot.start()
	httpFrontend = HTTPFrontend(8080, backend)
	httpFrontend.start()

if __name__ == '__main__' :
	main()
