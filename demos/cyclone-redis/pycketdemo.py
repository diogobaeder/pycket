#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2010 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

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
                'host' : 'localhost',
                'port' : 6379,
                'db_sessions' : 10,
                'db_notifications' : 11,
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
        self.write('<form method="post">Enter your username: <input name="username" type="text"><button type="submit" class="btn">Login</button></form>')


    def post(self):
        username = self.get_argument('username')
        if not username:
            self.write('<form method="post">Enter your username: <input name="username" type="text"><button type="submit" class="btn">Login</button></form>')
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
