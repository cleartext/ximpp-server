#!/usr/bin/env python

import datetime
import db

from models import User

from backend.base import Backend as BaseBackend
from backend.base import Message, message_compare
from utils import trace_methods


class Backend(BaseBackend):
    def __init__(self, domain):
        super(Backend, self).__init__()

        self.domain = domain
        self.messages = {}

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



    def getMessages(self, user):
        messages = []
        if self.messages.has_key(user):
            messages += self.messages[user]

        session = db.Session()
        user = session.query(User).filter(User.username == user).one()

        for contact in user.contacts():
            if self.messages.has_key(contact.username):
                messages += self.messages[contact.username]
        messages.sort(reverse=True, cmp=message_compare)
        return messages

    def getLastMessage(self, user):
        messages = self.getMessages(user)
        if len(messages) > 0:
            return messages[0]
        else:
            return Message(None, user, '')

    def addMessage(self, text, jid):
        user = self.getUserFromJID(jid)

        if len(text) > 0:
            # TODO save message in the database
            message = Message(datetime.datetime.utcnow(), user, text)
            self.notifyMessage(message, jid)

    def getAllUsers(self):
        session = db.Session()
        return [user.username for user in session.query(User)]

    def getContacts(self, user):
        session = db.Session()
        user = session.Query(User).filter(User.username == user).one()
        return user.contacts

    def getJIDForUser(self, user):
        return '%s@%s' % (user, self.domain)

    def getUserHasJID(self, user):
        session = db.Session()
        return session.query(User).filter(User.username == user).scalar() is not None

    def getShouldMonitorPresenceFromUser(self, user):
        # TODO: broken code, add database support
        return self.userPresenceMonitoring[user]

    def setShouldMonitorPresenceFromUser(self, user, state):
        # TODO: broken code, add database support
        self.userPresenceMonitoring[user] = state

    def getSubscriberJIDs(self, user):
        session = db.Session()
        user = session.query(User).filter(User.username == user).one()

        return [self.getJIDForUser(s.username) for s in user.subscribers]

    def getUserFromJID(self, user):
        #TODO fetch JID from database when it will be there
        return user.split('/',1)[0].split('@', 1)[0]

    def addContact(self, user, contact):
        session = db.Session()
        user = session.query(User).filter(User.username == user)
        contact = session.query(User).filter(User.username == contact)

        user.contacts.append(contact)
        session.commit()

    def registerXMPPUser(self, user, password, fulljid):
        barejid = fulljid.split('/', 1)[0]

        # TODO add code to save JID.
        session = db.Session()
        user = User(
            username = user,
            password = password,
            created_at = datetime.datetime.utcnow()
        )
        session.add(user)
        session.commit()
        return True

    def get_user_by_jid(self, jid, session = None):
        username = self.getUserFromJID(jid)
        user = session.query(User).filter(User.username == username).scalar()
        if user:
            user.jid = jid
        return user

    def get_user_by_username(self, username, session = None):
        return session.query(User).filter(User.username == username).scalar()

trace_methods(Backend)
