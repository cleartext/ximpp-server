import sys
import threading
import time
import unittest
import yaml
import sleekxmpp

from pdb import set_trace
from microblog.bot import Bot
from microblog import db

_bot = None


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        global _bot
        super(TestCase, self).__init__(*args, **kwargs)

        self.cfg = yaml.load(open(sys.argv[1]).read())
        db.init(self.cfg['database'])
        _bot = Bot(**self.cfg['component'])

        threading.Thread(target = _bot.start).start()


    def test_send_message(self):
        client = sleekxmpp.ClientXMPP('user2@coolananas.com.au', 'user2password')
        client.connect((self.cfg['component']['server'], self.cfg['component']['port']))
        client.sendMessage('user1@coolbananas.com.au', 'test')
        self.assertEqual(True, False)



if __name__ == '__main__':
    try:
        unittest.main(argv = sys.argv[:1])
    finally:
        time.sleep(1)
        if _bot is not None:
            _bot.stop()

