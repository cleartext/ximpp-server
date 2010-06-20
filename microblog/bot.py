import re
import logging
import datetime
import sleekxmpp.componentxmpp

from microblog import search
from microblog.db import db_session
from microblog.models import User, Message, SearchTerm
from microblog.utils import trace_methods
from microblog.exceptions import UserNotFound
from pdb import set_trace
from xml.etree import cElementTree as ET


class Payload(list):
    """ This class helps to extend cleartext's stanzas.
    """

    def _find_buddy_node(self):
        for node in self:
            if node.tag == '{http://cleartext.net/mblog}x':
                return node.find('{http://cleartext.net/mblog}buddy')


    def _set_text(self, text):
        if getattr(self, '_text', None) is None:
            buddy = self._find_buddy_node()
            if buddy is not None:
                self._text = ET.SubElement(buddy, '{http://cleartext.net/mblog}text')
        else:
            self._text.text = text


    def _get_text(self):
        _text = getattr(self, '_text', None)
        if _text is None:
            return None
        else:
            return _text.text


    text = property(_get_text, _set_text)


    def add_node(self, name, text = None):
        buddy = self._find_buddy_node()
        if buddy is not None:
            el = ET.SubElement(buddy, '{http://cleartext.net/mblog}' + name )
            if text is not None:
                el.text = text



class Commands(object):
    """
    Mixin with commands.
    """
    def _show_followers(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        if user:
            followers = list(user.subscribers)
            if followers:
                body = 'Your followers are:\n' + '\n'.join(
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
                body = 'Your contacts are:\n' + '\n'.join(
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
                self.xmpp.sendMessage(
                    user.jid,
                    'You don\'t follow @%s anymore.' % username,
                    mfrom = self.jid,
                    mtype = 'chat'
                )
                self.xmpp.sendMessage(
                    contact.jid,
                    'You lost one of your followers: @%s.' % user.username,
                    mfrom = self.jid,
                    mtype = 'chat'
                )
                return

        self.xmpp.sendMessage(
            user.jid,
            'You don\'t folow @%s.' % username,
            mfrom = self.jid,
            mtype = 'chat'
        )



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

        if contact in user.contacts:
            self.xmpp.sendMessage(
                user.jid,
                'You already follow @%s.' % username,
                mfrom = self.jid,
                mtype = 'chat'
            )
            return

        user.contacts.append(contact)
        session.commit()

        self.xmpp.sendMessage(
            user.jid,
            'Now you are following @%s.' % username,
            mfrom = self.jid,
            mtype = 'chat'
        )
        self.xmpp.sendMessage(
            contact.jid,
            'You have a new follower: @%s.' % user.username,
            mfrom = self.jid,
            mtype = 'chat'
        )


    def _whoami(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)
        body = 'Username: %s\nJID: %s' % (user.username, user.jid)
        self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _direct_message(self, event, username, message, session = None):
        user = self.get_user_by_username(username, session)
        from_ = self.get_user_by_jid(event['from'].jid, session)

        event.payload.text = message

        if user:
            body = 'Direct message from @%s: %s' % (from_.username, message)
            self.send_message(user.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)
        else:
            body = 'User @%s not found.' % username
            self.send_message(from_.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)


    def _reply_message(self, event, username, message, session = None):
        user = self.get_user_by_username(username, session)
        from_ = self.get_user_by_jid(event['from'].jid, session)

        if user:
            body = 'Reply from @%s: %s' % (from_.username, message)
            self.send_message(user.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)
        else:
            body = 'User @%s not found.' % username
            self.send_message(from_.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)


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
            body = 'Your searches:\n' + '\n'.join(
                t.term for t in terms
            )
        else:
            body = 'You have no searches.'
        self.xmpp.sendMessage(user.jid, body, mfrom = self.jid, mtype = 'chat')


    def _show_help(self, event, session = None):
        user = self.get_user_by_jid(event['from'].jid, session)

        self.xmpp.sendMessage(user.jid, self._COMMANDS_HELP, mfrom = self.jid, mtype = 'chat')


    _COMMANDS = [
        (r'^me$', _whoami, '"me" - shows who you are, your username and jid (Jabber ID)'),
        (r'^ers$', _show_followers, '"ers" - shows your followers'),
        (r'^ing$', _show_contacts, '"ing" - shows who you follow'),
        (r'^f (?P<username>\w+)$', _follow, '"f username" - follow this user'),
        (r'^u (?P<username>\w+)$', _unfollow, '"u username" - unfollow this user'),
        (r'^d (?P<username>\w+) (?P<message>.*)$', _direct_message, '"d username message text" - send direct message to the user'),
        (r'^@(?P<username>\w+) (?P<message>.*)$', _reply_message, '"@username message text" - mention a user, a public message to a user'),
        (r'^s$', _show_searches, '"s" - show saved searches'),
        (r'^s (?P<word>\w+)$', _add_search, '"s word" - save live search term'),
        (r'^us (?P<word>\w+)$', _remove_search, '"us word" - delete live search term'),
        (r'^help$', _show_help, '"help" - show this help'),
    ]

    _COMMANDS_HELP = 'Commands:\n  ' + '\n  '.join(
        help for regex, func, help in _COMMANDS
    )

    _COMMANDS = [(re.compile(regex, re.IGNORECASE), func, help)
                 for regex, func, help in _COMMANDS]


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
        user = session.query(User).filter(User.jid == jid).scalar()
        if user is None:
            raise UserNotFound('User with jid "%s" not found.' % jid)
        return user

    def get_user_by_username(self, username, session):
        user = session.query(User).filter(User.username == username).scalar()
        if user is None:
            raise UserNotFound('User with username "%s" not found.' % username)
        return user



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
        self.domain = jid.split('.', 1)[1]

        self.xmpp = ComponentXMPP(jid, password, server, port)
        self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)
        self.xmpp.add_event_handler('presence_subscribe',
                self.handle_presence_subscribe)
        self.xmpp.add_event_handler("presence_probe",
                self.handle_presence_probe)

        self.xmpp.add_event_handler('message', self._handle_message)

        for event in ['got_online', 'got_offline', 'changed_status']:
            self.xmpp.add_event_handler(event, self._handle_status_change)

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
    def _handle_message(self, event, session = None):
        try:
            payload = self._extract_payload(event)
            event.payload = payload

            if self._handle_commands(event, session) == False:
                self.handle_new_message(event, session)
                search.process_message(event)
        except Exception, e:
            self.log.exception('error during XMPP event processing')
            if self.debug:
                body = 'ERROR: %s' % e
                self.xmpp.sendMessage(event['from'].jid, body, mfrom = self.jid, mtype = 'chat')


    @db_session
    def _handle_status_change(self, event, session = None):
        # TODO think what to do on status change
        pass


    def handle_presence_probe(self, event):
        self.xmpp.sendPresence(pto = event["from"].jid)


    def handle_presence_subscribe(self, subscription):
        user_jid = subscription['from'].jid
        user_domain = user_jid.rsplit('@', 1)[1]

        if user_domain == self.domain:
            self.xmpp.sendPresenceSubscription(pto = user_jid, ptype='subscribed')
            self.xmpp.sendPresence(pto = user_jid)
            self.xmpp.sendPresenceSubscription(pto = user_jid, ptype='subscribe')
        else:
            self.log.warning(
                'Access denied for user %s, because this bot service on the domain %s.' % \
                (user_jid, self.domain)
            )
            self.xmpp.sendPresenceSubscription(pto = user_jid, ptype = 'unsubscribed')


    def _extract_payload(self, event):
        payload = Payload(filter(lambda x: x.tag.endswith('}x'), event.getPayload()))
        payload.text = event['body']
        return payload


    def handle_new_message(self, event, session):
        text = event['body']
        from_user = self.get_user_by_jid(event['from'].jid, session)

        body = '@%s: %s' % (from_user.username, text)
        for subscriber in from_user.subscribers:
            self.send_message(subscriber.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)

        body = 'Mention by @%s: %s' % (from_user.username, text)
        for username in re.findall(r'@\w+', text):
            user = self.get_user_by_username(username[1:], session)
            if user not in from_user.subscribers:
                self.send_message(user.jid, body, mfrom = self.jid, mtype = 'chat', payload = event.payload)


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
