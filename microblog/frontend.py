import logging
import base64
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import escape

from microblog.db import db_session
from microblog.db_helpers import \
    get_user_by_username, \
    get_all_users
from microblog.models import User
from pdb import set_trace


class Handler(tornado.web.RequestHandler, DBHelpers):
    def get_template_path(self):
        path = self.application.settings.get('template_path')
        if path[0] != '/':
            path = os.path.join(
                os.path.dirname(__file__),
                path
            )
        return path


    def render(self, template, **kwargs):
        def _escape(value):
            return escape.xhtml_escape(unicode(value))
        kwargs['escape'] = _escape
        return super(Handler, self).render(template, **kwargs)



class FrontPage(Handler):
    @db_session
    def get(self, session = None):
        self.render(
            'index.html',
            users = get_all_users(session)
        )



class User(Handler):
    @db_session
    def get(self, username, session = None):
        user = get_user_by_username(username, session)
        self.render(
            'user.html',
            user = user,
            vcard = user.vcard,
        )


class Avatar(Handler):
    @db_session
    def get(self, username, session = None):
        user = get_user_by_username(username, session)
        vc = user.vcard
        if vc is None or vc.PHOTO is None:
            raise tornado.web.HTTPError(404)
        else:
            message = base64.standard_b64decode(vc.PHOTO.BINVAL.text)
            self.set_header('Content-Type', vc.PHOTO.TYPE or 'image/jpeg')

        self.write(message)



class Frontend(object):
    def __init__(self, port = 8888, **tornado_settings):
        self.port = port
        self.tornado_settings = tornado_settings
        self.log = logging.getLogger('frontend')

    def start(self):
        self.log.debug('Starting frontend.')

        application = tornado.web.Application([
            (r'/', FrontPage),
            (r'/user/(\w+)/', User),
            (r'/user/(\w+)/avatar/', Avatar),
        ], **self.tornado_settings)

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()

