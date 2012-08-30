"""
Cyclone Redis Demo

This demonstrates integrating pycket with cyclone, using a redis
backend (but easily switched to using memcached).

"""

import sys

import cyclone.auth
import cyclone.escape
import cyclone.web

from twisted.python import log
from twisted.internet import reactor
from pycket.session import SessionMixin


class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/auth/login", AuthHandler),
            (r"/auth/logout", LogoutHandler),
        ]
        settings = dict(
            cookie_secret="32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            debug=True,
            login_url="/auth/login",
            logout_url="/auth/logout",
        )

        settings['pycket'] = {
            'engine': 'redis',
            'storage': {
                'host': 'localhost',
                'port': 6379,
                'db_sessions': 10,
                'db_notifications': 11
            }
        }

        cyclone.web.Application.__init__(self, handlers, **settings)


class BaseHandler(cyclone.web.RequestHandler, SessionMixin):
    def get_current_user(self):
        user = self.session.get('user')
        if not user:
            return None
        return user


class MainHandler(BaseHandler):
    @cyclone.web.authenticated
    def get(self):
        name = cyclone.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)
        self.write("<br><br><a href=\"/auth/logout\">Log out</a>")


class AuthHandler(BaseHandler, SessionMixin):

    def get(self):
        self.write('<form method="post">'
                   'Enter your username: <input name="username" type="text">'
                   '<button type="submit" class="btn">Login</button></form>')

    def post(self):
        username = self.get_argument('username')
        if not username:
            self.write('<form method="post">Enter your username: '
                       '<input name="username" type="text">'
                       '<button type="submit" class="btn">Login</button>'
                       '</form>')
        else:
            self.session.set('user', username)
            self.redirect('/')


class LogoutHandler(BaseHandler, SessionMixin):
    def get(self):
        self.session.delete('user')
        self.redirect("/")


def main():
    log.startLogging(sys.stdout)
    reactor.listenTCP(8888, Application(), interface="127.0.0.1")
    reactor.run()


if __name__ == "__main__":
    main()
