import re
import logging
import sleekxmpp.componentxmpp

from xml.etree import cElementTree as ET
from pdb import set_trace

from utils import trace_methods
from db import db_session
from models import User


class Commands(object):
    """
    Mixin with commands.
    """
    def _show_followers(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        if user:
            followers = list(user.subscribers)
            if followers:
                body = 'You followers are:\n' + '\n'.join(
                    f.username for f in followers
                )
            else:
                body = 'You have no followers.'
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _show_contacts(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        if user:
            contacts = list(user.contacts)
            if contacts:
                body = 'You contacts are:\n' + '\n'.join(
                    f.username for f in contacts
                )
            else:
                body = 'You have no contacts.'
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _unfollow(self, event, username, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        contact = self.get_user_by_username(username, session)

        if not contact:
            body = 'User @%s not found.' % username
            self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')
            return

        for idx, u in enumerate(user.contacts):
            if u.username == contact.username:
                user.contacts.pop(idx)
                session.commit()
                self.xmpp.sendMessage(user.jid, 'done', mfrom = self.jid, mtype = 'chat')
                return

        body = 'You don\'t folow @%s' % username
        self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')



    def _follow(self, event, username, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        contact = self.get_user_by_username(username, session)

        if not contact:
            body = 'User @%s not found.' % username
            self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')
            return

        if user == contact:
            body = 'You can\'t follow youself.'
            self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')
            return

        user.contacts.append(contact)
        session.commit()

        self.xmpp.sendMessage(user.jid, 'done', mfrom = self.jid, mtype = 'chat')


    def _whoami(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        body = 'Username: %s\nJID: %s' % (user.username, user.jid)
        self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _direct_message(self, event, username, message, session = None):
        user = self.get_user_by_username(username, session)
        from_ = self.get_user_by_jid(event['from'].jid, session)

        if user:
            body = 'Direct from @%s: %s' % (from_.username, message)
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')
        else:
            body = 'User @%s not found.' % username
            self.xmpp.sendMessage(from_.jid, body, mfrom = self.jid, mtype = 'chat')


    def _reply_message(self, event, username, message, session = None):
        user = self.get_user_by_username(username, session)
        from_ = self.get_user_by_jid(event['from'].jid, session)

        if user:
            body = 'Reply from @%s: %s' % (from_.username, message)
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')
        else:
            body = 'User @%s not found.' % username
            self.xmpp.sendMessage(from_.jid, body, mfrom = self.jid, mtype = 'chat')


    _COMMANDS = [
        (r'^ers$', _show_followers),
        (r'^ing$', _show_contacts),
        (r'^me$', _whoami),
        (r'^u (?P<username>\w+)$', _unfollow),
        (r'^f (?P<username>\w+)$', _follow),
        (r'^d (?P<username>\w+) (?P<message>.*)$', _direct_message),
        (r'^@(?P<username>\w+) (?P<message>.*)$', _reply_message),
    ]

    _COMMANDS = [(re.compile(regex), func) for regex, func in _COMMANDS]


    def _handle_commands(self, event, session):
        """ Checks if event contains controls sequence.
            If it is, then True returned and command is processed,
            otherwise, method returns False.
        """
        message = event['body']

        for regex, func in self._COMMANDS:
            match = regex.match(message)
            if match is not None:
                func(self, event, session = session, **match.groupdict())
                return True

        return False


class DBHelpers(object):
    """
    Mixin with different database helpers, to retrive
    information about users.
    """
    def get_all_users(self, session):
        return session.query(User)

    def get_user_by_jid(self, jid, session):
        username = jid.split('/',1)[0].split('@', 1)[0]
        return session.query(User).filter(User.username == username).scalar()

    def get_user_by_username(self, username, session):
        return session.query(User).filter(User.username == username).scalar()


class Bot(Commands, DBHelpers):
    def __init__(self, jid, password, server, port, debug = False):
        self.jid = jid
        self.xmpp = sleekxmpp.componentxmpp.ComponentXMPP(jid, password, server, port)
        self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)
        self.xmpp.add_event_handler("changed_subscription",
                self.handleXMPPPresenceSubscription)
        self.xmpp.add_event_handler("got_presence_probe",
                self.handleXMPPPresenceProbe)
        for event in ["message", "got_online", "got_offline", "changed_status"]:
            self.xmpp.add_event_handler(event, self.handleIncomingXMPPEvent)
        ## BEGIN NEW
        self.xmpp.registerPlugin("xep_0030")
        ## END NEW
        self.log = logging.getLogger('bot')
        self.debug = debug


    @db_session
    def handleXMPPConnected(self, event, session = None):
        for user in self.get_all_users(session):
            self.log.debug('sending presence to jid "%s"' % user.jid)
            self.xmpp.sendPresence(pto = user.jid)

    @db_session
    def handleIncomingXMPPEvent(self, event, session = None):
        try:
            type_ = event['type']

            if type_ == 'chat':
                if self._handle_commands(event, session) == False:
                    text = event['body']
                    user = self.get_user_by_jid(event['from'].jid, session)
                    message = Message(datetime.datetime.utcnow(), user, text)
                    self.handle_new_message(message, session)
            else:
                self.log.error(ET.tostring(event.xml))
        except Exception, e:
            self.log.exception('error during XMPP event processing')
            if self.debug:
                body = 'ERROR: %s' % e
                self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')


    def handleXMPPPresenceProbe(self, event):
        self.xmpp.sendPresence(pto = event["from"].jid)

    def handleXMPPPresenceSubscription(self, subscription):
        if subscription["type"] == "subscribe":
            userJID = subscription["from"].jid
            self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribed")
            self.xmpp.sendPresence(pto = userJID)
            self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribe")


    def handle_new_message(self, message, session):
        body = '@%s: %s' % (message.user.username, message.text)
        for subscriber in message.user.subscribers:
            self.xmpp.sendMessage(subscriber.jid, body, mfrom = self.jid, mtype = 'chat')

        body = 'Mention by @%s: %s' % (message.user.username, message.text)
        for username in re.findall(r'@\w+', message.text):
            user = self.get_user_by_username(username[1:], session)
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')

    def start(self):
        self.xmpp.connect()
        self.xmpp.process(threaded = False)

    def stop(self):
        self.xmpp.disconnect()


trace_methods(Bot)
