import copy
import threading
import logging

from Queue import Queue
from collections import defaultdict
from microblog.db import db_session
from microblog.models import SearchTerm
from sqlalchemy.orm.exc import NoResultFound

from pdb import set_trace

_searches = defaultdict(set)
_queue = Queue()

class Sentinel(object): pass


@db_session
def add_search(word, username, session = None):
    word = word.lower()

    log = logging.getLogger('search')
    log.debug('New search term "%s" for username "%s"' % (word, username))
    _searches[word].add(username)

    session.add(SearchTerm(word, username))


@db_session
def remove_search(word, username, session = None):
    word = word.lower()

    log = logging.getLogger('search')
    log.debug('Removing search term "%s" for username "%s"' % (word, username))
    _searches[word].discard(username)

    try:
        term = session.query(SearchTerm).filter(SearchTerm.term == word).filter(
            SearchTerm.username == username
        ).one()
    except NoResultFound:
        return

    session.delete(term)


def process_message(event):
    if event.getType() == 'chat':
        log = logging.getLogger('search')
        log.debug('Adding text to the queue: "%s"' % event['body'])
        _queue.put(event)


def stop():
    log = logging.getLogger('search')
    log.debug('Trying to stop search thread')
    _queue.put(Sentinel)


@db_session
def start(bot, session = None):
    log = logging.getLogger('search')

    log.debug('Loading search terms.')

    count = 0
    for term in session.query(SearchTerm).all():
        _searches[term.term].add(term.username)
        count += 1
    log.debug('%d terms were loaded' % count)

    @db_session
    def _process_event(event, session = None):
        log.debug('Processing word "%s"' % event['body'])

        text = event['body']
        from_user = bot.get_user_by_jid(event['from'].jid, session)

        body = 'Search: @%s says "%s"' % (from_user.username, text)

        num_recipients = 0

        text = text.lower()
        receivers = set()

        for word, users in _searches.iteritems():
            if word in text:
                receivers.update(users)

        payload = copy.deepcopy(event.payload)
        payload.add_node('search-result')

        for user in receivers:
            user = bot.get_user_by_username(user, session)
            if user not in from_user.subscribers and \
                    user != from_user:
                num_recipients += 1
                bot.send_message(user.jid, body, mfrom = bot.jid, mtype = 'chat', payload = payload)

        log.debug('This message was received by %s recipients.' % num_recipients)


    def _worker():
        log.debug('Starting search thread.')
        while True:
            event = _queue.get()

            if event is Sentinel:
                log.debug('Stopping search thread.')
                break

            try:
                _process_event(event)
            except:
                log.exception('Error during _process_event')


    thread = threading.Thread(target = _worker)
    thread.start()

