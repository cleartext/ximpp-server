#!/usr/bin/env python

import datetime
import db

from models import User

from backend.base import Backend as BaseBackend
from backend.base import Message, message_compare


class Backend(BaseBackend):
    def __init__(self, domain):
        super(Backend, self).__init__()

        self.domain = domain
        self.messages = {}
        self.contacts = {}

        # Dummy data
        self.messages = {
            'peter': [
                Message(datetime.datetime(2008, 01, 01), 'peter', 'Reading some XMPP specs'),
                Message(datetime.datetime(2008, 01, 03), 'peter', '@kevin Tell me about it')
            ],
            'kevin': [
                Message(datetime.datetime(2008, 01, 02), 'kevin', 'Too little time to do all the things I want to')
            ],
            'remko': [
                Message(datetime.datetime(2008, 01, 04), 'remko', 'Woohoow, holidays!')
            ]
        }
        self.contacts = { 'remko': ['kevin', 'peter'] }
        self.subscribers = { 'kevin': ['remko'], 'peter': ['remko'] }

        session = db.Session()

        self.jidToUser = {}
        self.userToJID = {}
        self.userPresenceMonitoring = {}

        for user in session.query(User):
            username = user.username
            self.log.debug('Reading user "%s"' % username)

            jid = '%s@%s' % (username, self.domain)
            self.jidToUser[jid] = username
            self.userToJID[username] = jid

            self.userPresenceMonitoring[username] = True


    def getMessages(self, user):
        messages = []
        if self.messages.has_key(user):
            messages += self.messages[user]

        for contact in self.contacts.get(user, []):
            if self.messages.has_key(contact):
                messages += self.messages[contact]
        messages.sort(reverse=True, cmp=message_compare)
        return messages

    def getLastMessage(self, user):
        messages = self.getMessages(user)
        if len(messages) > 0:
            return messages[0]
        else:
            return Message(None, user, '')

    def addMessageFromUser(self, text, user):
        if len(text) > 0 and self.getLastMessage(user) != text:
            message = Message(datetime.datetime.today(), user, text)
            self.messages.setdefault(user,[]).append(message)
            self.notifyMessage(message)

    def getAllUsers(self):
        return self.messages.keys()

    def getContacts(self, user):
        return self.contacts.get(user, [])

    def getJIDForUser(self, user):
        return self.userToJID[user]

    def getUserHasJID(self, user):
        return self.userToJID.has_key(user)

    def getShouldMonitorPresenceFromUser(self, user):
        return self.userPresenceMonitoring[user]

    def setShouldMonitorPresenceFromUser(self, user, state):
        self.userPresenceMonitoring[user] = state

    def getSubscriberJIDs(self, user):
        subscribers = []
        #for subscriber in self.subscribers.get(user, []) + [user]:
        for subscriber in self.subscribers.get(user, []):
            if self.userToJID.has_key(subscriber):
                subscribers.append(self.userToJID[subscriber])
        return subscribers

    def getUserFromJID(self, user):
        return self.jidToUser.get(user.split('/',1)[0], None)

    def addContact(self, user, contact):
        if not self.contacts.has_key(user):
            self.contacts[user] = []
        self.contacts.setdefault(user, []).append(contact)

    def registerXMPPUser(self, user, password, fulljid):
        barejid = fulljid.split('/', 1)[0]
        self.jidToUser[barejid] = user
        self.userToJID[user] = barejid
        return True

