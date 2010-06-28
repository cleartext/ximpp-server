import logging
import base64
import tornado.httpserver
import tornado.ioloop
import tornado.web

from microblog.db import db_session
from microblog.db_helpers import DBHelpers
from microblog.models import User
from pdb import set_trace


class MainHandler(tornado.web.RequestHandler, DBHelpers):
    @db_session
    def get(self, session = None):
        message = '<h1>Cleartext Microblogging.</h1>'
        message += 'Users:<br/><br/>'
        message += '<br/>'.join('<a href="/user/%s/">%s</a>' % \
            (user.username, user.username) \
            for user in self.get_all_users(session))
        self.write(message)



class UserHandler(tornado.web.RequestHandler, DBHelpers):
    @db_session
    def get(self, username, session = None):
        message = '<h1>Cleartext Microblogging.</h1>'
        message += '<h2>%s</h2>' % username
        message += '<img src="avatar/" /><br/>'
        user = self.get_user_by_username(username, session)

        vc = user.vcard
        if vc is None:
            message += 'no vCard'
        else:
            message += 'vCard: FN = %s, NICKNAME = %s' % (vc.FN.text, vc.NICKNAME.text)

        self.write(message)


class AvatarHandler(tornado.web.RequestHandler, DBHelpers):
    @db_session
    def get(self, username, session = None):
        user = self.get_user_by_username(username, session)
        vc = user.vcard
        if vc is None or vc.PHOTO is None:
            raise tornado.web.HTTPError(404)
        else:
            message = base64.standard_b64decode(vc.PHOTO.BINVAL.text)
            self.set_header('Content-Type', vc.PHOTO.TYPE.text or 'image/jpeg')

        self.write(message)



class Frontend(object):
    def __init__(self, port = 8888):
        self.port = port
        self.log = logging.getLogger('frontend')

    def start(self):
        self.log.debug('Starting frontend.')

        application = tornado.web.Application([
            (r'/', MainHandler),
            (r'/user/(\w+)/', UserHandler),
            (r'/user/(\w+)/avatar/', AvatarHandler),
        ])

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()

