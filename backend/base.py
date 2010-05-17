""" Base primitives for the  backends. """

import logging

def message_compare(m1, m2):
    return cmp(m1.date, m2.date)


class Message(object):
    def __init__(self, date, user, text):
        self.date = date
        self.user = user
        self.text = text


class Backend(object):
    def __init__(self):
        self.handlers = []
        self.log = logging.getLogger('backend')

    def addMessageHandler(self, handler):
        self.handlers.append(handler)

    def notifyMessage(self, message, from_jid):
        for handler in self.handlers:
            handler(message, from_jid)
