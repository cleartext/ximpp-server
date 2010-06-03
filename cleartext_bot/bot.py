import re
import logging
import datetime
import sleekxmpp.componentxmpp

from xml.etree import cElementTree as ET
from pdb import set_trace

from utils import trace_methods
from db import db_session
from models import User, Message, SearchTerm

import search

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


    def _add_search(self, event, word, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        search.add_search(word, user.username)
        self.xmpp.sendMessage(user.jid, 'Now you are looking for "%s" in all messages' % word, mfrom = self.jid, mtype = 'chat')


    def _remove_search(self, event, word, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        search.remove_search(word, user.username)
        self.xmpp.sendMessage(user.jid, 'Search on "%s" was dropped' % word, mfrom = self.jid, mtype = 'chat')


    def _show_searches(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        terms = session.query(SearchTerm).filter(SearchTerm.username == user.username)

        if terms.count() > 0:
            body = 'You searches:\n' + '\n'.join(
                t.term for t in terms
            )
        else:
            body = 'You have no searches.'
        self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _show_help(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)

        self.xmpp.sendMessage(user.jid, self._COMMANDS_HELP, mfrom = self.jid, mtype = 'chat')


    _COMMANDS = [
        (r'^me$', _whoami, '"me" - shows who you are, your username and jid'),
        (r'^ers$', _show_followers, '"ers" - shows your followers'),
        (r'^ing$', _show_contacts, '"ing" - shows who you follow'),
        (r'^f (?P<username>\w+)$', _follow, '"f some_username" - follow this user'),
        (r'^u (?P<username>\w+)$', _unfollow, '"u some_username" - unfollow this user'),
        (r'^d (?P<username>\w+) (?P<message>.*)$', _direct_message, '"d some_username message text" - send direct message to the user'),
        (r'^@(?P<username>\w+) (?P<message>.*)$', _reply_message, '"@username message text" - same as direct message'),
        (r'^s$', _show_searches, '"s" - show saved searches'),
        (r'^s (?P<word>\w+)$', _add_search, '"s word" - save live search term'),
        (r'^us (?P<word>\w+)$', _remove_search, '"us word" - delete live search term'),
        (r'^help$', _show_help, '"help" - show this help'),
    ]

    _COMMANDS_HELP = 'Commands:\n  ' + '\n  '.join(
        help for regex, func, help in _COMMANDS
    )

    _COMMANDS = [(re.compile(regex), func, help) for regex, func, help in _COMMANDS]


    def _handle_commands(self, event, session):
        """ Checks if event contains controls sequence.
            If it is, then True returned and command is processed,
            otherwise, method returns False.
        """
        message = event['body']

        for regex, func, help in self._COMMANDS:
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
        jid = jid.split('/', 1)[0]
        return session.query(User).filter(User.jid == jid).scalar()

    def get_user_by_username(self, username, session):
        return session.query(User).filter(User.username == username).scalar()



class ComponentXMPP(sleekxmpp.componentxmpp.ComponentXMPP):
    """ Wrapper around sleekxmpp's component.
        Used to stop all threads on disconnect.
    """

    def disconnect(self, reconnect = False):
        super(ComponentXMPP, self).disconnect(reconnect)
        if not reconnect:
            search.stop()



class Bot(Commands, DBHelpers):
    def __init__(self, jid, password, server, port, debug = False):
        self.jid = jid
        self.xmpp = ComponentXMPP(jid, password, server, port)
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

        search.start(self)


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
                    self.handle_new_message(event, session)
                    search.process_message(event)
            else:
                self.log.error('unknown event type "%s":\n%s' % (type_, ET.tostring(event.xml)))
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

    def _extract_payload(self, event):
        return filter(lambda x: x.tag.endswith('}x'), event.getPayload())


    def handle_new_message(self, event, session):
        text = event['body']
        user = self.get_user_by_jid(event['from'].jid, session)

        payload = self._extract_payload(event)

        body = '@%s: %s' % (user.username, text)
        for subscriber in user.subscribers:
            self.send_message(subscriber.jid, body, mfrom = self.jid, mtype = 'chat', payload = payload)

        body = 'Mention by @%s: %s' % (user.username, text)
        for username in re.findall(r'@\w+', text):
            user = self.get_user_by_username(username[1:], session)
            self.send_message(user.jid, body, mfrom = self.jid, mtype = 'chat', payload = payload)


    def send_message(self, mto, mbody,
            msubject = None, mtype = None, mhtml = None,
            mfrom = None, mnick = None, payload = []):

        msg = self.xmpp.makeMessage(mto,mbody,msubject,mtype,mhtml,mfrom,mnick)
        for item in payload:
            msg.setPayload(item)
        self.xmpp.send(msg)


    def start(self):
        self.xmpp.connect()
        self.xmpp.process(threaded = False)

    def stop(self):
        search.stop()
        self.xmpp.disconnect()


trace_methods(Bot)
