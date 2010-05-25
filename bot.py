import re
import logging
import sleekxmpp.componentxmpp

from xml.etree import cElementTree as ET
from pdb import set_trace
from utils import trace_methods
from db import db_session


def _show_followers(bot, event, session = None):
    user = bot.backend.get_user_by_jid(event['from'].jid, session)
    if user:
        followers = list(user.subscribers)
        if followers:
            body = 'You followers are:\n' + '\n'.join(
                f.username for f in followers
            )
        else:
            body = 'You have no followers.'
        bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')


def _show_contacts(bot, event, session = None):
    user = bot.backend.get_user_by_jid(event['from'].jid, session)
    if user:
        contacts = list(user.contacts)
        if contacts:
            body = 'You contacts are:\n' + '\n'.join(
                f.username for f in contacts
            )
        else:
            body = 'You have no contacts.'
        bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')


def _unfollow(bot, event, username, session = None):
    user = bot.backend.get_user_by_jid(event['from'].jid, session)
    contact = bot.backend.get_user_by_username(username, session)

    if not contact:
        body = 'User @%s not found.' % username
        bot.xmpp.sendMessage(event['from'].jid, body, mfrom = bot.jid, mtype = 'chat')
        return

    for idx, u in enumerate(user.contacts):
        if u.username == contact.username:
            user.contacts.pop(idx)
            session.commit()
            bot.xmpp.sendMessage(user.jid, 'done', mfrom = bot.jid, mtype = 'chat')
            return

    body = 'You don\'t folow @%s' % username
    bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')



def _follow(bot, event, username, session = None):
    user = bot.backend.get_user_by_jid(event['from'].jid, session)
    contact = bot.backend.get_user_by_username(username, session)

    if not contact:
        body = 'User @%s not found.' % username
        bot.xmpp.sendMessage(event['from'].jid, body, mfrom = bot.jid, mtype = 'chat')
        return

    if user == contact:
        body = 'You can\'t follow youself.'
        bot.xmpp.sendMessage(event['from'].jid, body, mfrom = bot.jid, mtype = 'chat')
        return

    user.contacts.append(contact)
    session.commit()

    bot.xmpp.sendMessage(user.jid, 'done', mfrom = bot.jid, mtype = 'chat')


def _whoami(bot, event, session = None):
    user = bot.backend.get_user_by_jid(event['from'].jid, session)
    body = 'Username: %s\nJID: %s' % (user.username, user.jid)
    bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')


def _direct_message(bot, event, username, message, session = None):
    user = bot.backend.get_user_by_username(username, session)
    from_ = bot.backend.get_user_by_jid(event['from'].jid, session)

    if user:
        body = 'Direct from @%s: %s' % (from_.username, message)
        bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')
    else:
        body = 'User @%s not found.' % username
        bot.xmpp.sendMessage(from_.jid, body, mfrom = bot.jid, mtype = 'chat')


def _reply_message(bot, event, username, message, session = None):
    user = bot.backend.get_user_by_username(username, session)
    from_ = bot.backend.get_user_by_jid(event['from'].jid, session)

    if user:
        body = 'Reply from @%s: %s' % (from_.username, message)
        bot.xmpp.sendMessage(user.jid, body, mfrom = bot.jid, mtype = 'chat')
    else:
        body = 'User @%s not found.' % username
        bot.xmpp.sendMessage(from_.jid, body, mfrom = bot.jid, mtype = 'chat')


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


class Bot(object):
    def __init__(self, jid, password, server, port, backend = None, debug = False):
        self.jid = jid
        self.xmpp = sleekxmpp.componentxmpp.ComponentXMPP(jid, password, server, port)
        self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)
        self.xmpp.add_event_handler("changed_subscription",
                self.handleXMPPPresenceSubscription)
        self.xmpp.add_event_handler("got_presence_probe",
                self.handleXMPPPresenceProbe)
        for event in ["message", "got_online", "got_offline", "changed_status"]:
            self.xmpp.add_event_handler(event, self.handleIncomingXMPPEvent)
        self.backend = backend
        self.backend.addMessageHandler(self.handleMessageAddedToBackend)
        ## BEGIN NEW
        self.xmpp.registerPlugin("xep_0030")
        ## END NEW
        self.log = logging.getLogger('bot')
        self.debug = debug


    def handleXMPPConnected(self, event):
        for user in self.backend.getAllUsers():
            if self.backend.getUserHasJID(user):
                jid = self.backend.getJIDForUser(user)
                self.log.debug('sending presence to user "%s" with jid "%s"' % (user, jid))
                self.xmpp.sendPresence(pto = jid)
            else:
                self.log.debug('"user %s" has no jid' % user)

    @db_session
    def handleIncomingXMPPEvent(self, event, session = None):
        try:
            type_ = event['type']

            if type_ == 'chat':
                if self._handle_commands(event, session) == False:
                    message = event['body']
                    self.backend.addMessage(message, event['from'].jid)
            else:
                self.log.error(ET.tostring(event.xml))
        except Exception, e:
            self.log.exception('error during XMPP event processing')
            if self.debug:
                body = 'ERROR: %s' % e
                self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')


    def _handle_commands(self, event, session):
        """ Checks if event contains controls sequence.
            If it is, then True returned and command is processed,
            otherwise, method returns False.
        """
        message = event['body']

        for regex, func in _COMMANDS:
            match = regex.match(message)
            if match is not None:
                func(self, event, session = session, **match.groupdict())
                return True

        return False


    def handleXMPPPresenceProbe(self, event):
        self.xmpp.sendPresence(pto = event["from"].jid)

    def handleXMPPPresenceSubscription(self, subscription):
        if subscription["type"] == "subscribe":
            userJID = subscription["from"].jid
            self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribed")
            self.xmpp.sendPresence(pto = userJID)
            self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribe")


    @db_session
    def handleMessageAddedToBackend(self, message, from_jid, session):
        body = '@%s: %s' % (message.user, message.text)
        for subscriberJID in self.backend.getSubscriberJIDs(message.user):
            self.xmpp.sendMessage(subscriberJID, body, mfrom = self.jid, mtype = 'chat')

        body = 'Mention by @%s: %s' % (message.user, message.text)
        for username in re.findall(r'@\w+', message.text):
            user = self.backend.get_user_by_username(username[1:], session)
            self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def start(self):
        self.xmpp.connect()
        self.xmpp.process(threaded = False)

    def stop(self):
        self.xmpp.disconnect()


trace_methods(Bot)
