import logging
import base64
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import escape
from collections import defaultdict

from microblog.db import Session
from microblog.db_helpers import \
    get_user_by_username, \
    get_all_users
from microblog.exceptions import UserNotFound
from microblog.models import User
from pdb import set_trace


class Handler(tornado.web.RequestHandler):
    need_db_session = True

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self._session = Session()


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


    def get_current_user(self):
        username = self.get_secure_cookie('session')
        if username:
            return get_user_by_username(username, self._session)
        return None


    def finish(self, *args, **kwargs):
        super(Handler, self).finish(*args, **kwargs)
        if self._session is not None:
            self._session.commit()
            self._session.close()


    def send_error(self, *args, **kwargs):
        if self._session is not None:
            self._session.rollback()
            self._session.close()
            self._session = None
        super(Handler, self).send_error(*args, **kwargs)



class FrontPage(Handler):
    def get(self):
        self.render(
            'index.html',
            users = get_all_users(self._session)
        )



class User(Handler):
    def get(self, username):
        user = get_user_by_username(username, self._session)
        self.render(
            'user.html',
            user = user,
            vcard = user.vcard,
        )



class Avatar(Handler):
    def get(self, username):
        user = get_user_by_username(username, self._session)
        vc = user.vcard
        if vc is None or vc.PHOTO is None:
            raise tornado.web.HTTPError(404)
        else:
            message = base64.standard_b64decode(vc.PHOTO.BINVAL.text)
            self.set_header('Content-Type', vc.PHOTO.TYPE or 'image/jpeg')

        self.write(message)



class Login(Handler):
    def get(self):
        next = self.get_argument('next', '/')
        self.render('login.html', next = next)

    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        next = self.get_argument('next', '/')

        errors = defaultdict(unicode)
        try:
            user = get_user_by_username(username, self._session)
        except UserNotFound:
            errors['username'] = 'User not found.'
        else:
            if user.password == password:
                self.set_secure_cookie('session', username)
                self.redirect(next)
                return
            else:
                errors['password'] = 'Password mismatch.'

        self.render('login.html', next = next, errors = errors)



class Logout(Handler):
    def get(self):
        next = self.get_argument('next', '/')
        self.render('logout.html', next = next)

    def post(self):
        next = self.get_argument('next', '/')
        self.clear_cookie('session')
        self.redirect(next)



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
            (r'/login/', Login),
            (r'/logout/', Logout),
        ], **self.tornado_settings)

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()

