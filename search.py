import threading
from Queue import Queue
from collections import defaultdict
import logging
import db

_searches = defaultdict(list)
_queue = Queue()

class Sentinel(object): pass


def add_search(word, username):
    log = logging.getLogger('search')
    log.debug('New search term "%s" for username "%s"' % (word, username))
    _searches[word.lower()].append(username)


def process_message(event):
    log = logging.getLogger('search')
    log.debug('Adding text to the queue: "%s"' % event['body'])
    _queue.put(event)


def stop():
    log = logging.getLogger('search')
    log.debug('Trying to stop search thread')
    _queue.put(Sentinel)


def start(bot):
    log = logging.getLogger('search')

    def _worker():
        log.debug('Starting search thread.')
        while True:
            event = _queue.get()
            session = db.Session()
            if event is Sentinel:
                log.debug('Stopping search thread.')
                break

            log.debug('Processing word "%s"' % event['body'])

            text = event['body']
            from_user = bot.get_user_by_jid(event['from'].jid, session)

            body = 'Search: @%s says "%s"' % (from_user.username, text)
            payload = bot._extract_payload(event)

            num_recipients = 0

            text = text.lower()
            for word, users in _searches.iteritems():
                if word in text:
                    num_recipients += len(users)
                    for user in users:
                        user = bot.get_user_by_username(user, session)
                        bot.send_message(user.jid, body, mfrom = bot.jid, mtype = 'chat', payload = payload)

            log.debug('This message was received by %s recipients.' % num_recipients)

    thread = threading.Thread(target = _worker)
    thread.start()

