'''
This module contains SessionMixin, which can be used in RequestHandlers, and
SessionManager, which is the real session manager, and is referenced by the
SessionMixin.

It's mandatory that you set the "cookie_secret" in your application settings,
because the session ID is stored in a secure manner.

If you want to change the settings that are passed to the Redis client, set a
"pycket_redis" dictionary with the intended Redis settings in your Tornado
application settings. All these settings are passed to the redis.Redis client
(except for the "db" parameter, which is always set to "pycket_sessions").

If you want to change the cookie settings passed to the handler, set a
"pycket_cookies" setting with the items you want. This is also valid for
"expires" and "expires_days", which, by default, will be None, therefore making
the sessions expire on browser close, but, if you set them, your custom values
will override the default behaviour.
'''

import pickle
from uuid import uuid4

import redis

class SessionManager(object):
    '''
    This is the real class that manages sessions. All session objects are
    persisted in a Redis database, inside a bucket called "pycket_sessions".
    After 1 day without changing a session, it's purged from the bucket,
    to avoid it to grow out-of-control.

    When a session is started, a cookie named 'PYCKET_ID' is set, containing the
    encrypted session id of the user. By default, it's cleaned every time the
    user closes the browser.

    The recommendation is to use the manager instance that comes with the
    SessionMixin (using the "session" property of the handler instance), but it
    can be instantiated ad-hoc.
    '''

    SESSION_ID_NAME = 'PYCKET_ID'
    DB_NAME = 'pycket_sessions'
    EXPIRE_SECONDS = 24 * 60 * 60

    def __init__(self, handler):
        '''
        Expects a tornado.web.RequestHandler
        '''

        self.handler = handler
        redis_settings = handler.settings.get('pycket_redis', {})
        redis_settings['db'] = self.DB_NAME
        self.bucket = redis.Redis(**redis_settings)

    def set(self, name, value):
        '''
        Sets a value for "name". It may be any pickable (see "pickle" module
        documentation) object.
        '''

        def change(session):
            session[name] = value
        self.__change_session(change)

    def get(self, name, default=None):
        '''
        Gets the object for "name", or None if there's no such object. If
        "default" is provided, return it if no object is found.
        '''

        session = self.__get_session_from_db()

        return session.get(name, default)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError('%s not found in bucket' % key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def delete(self, name):
        '''
        Deletes the object with "name" from the session, if exists.
        '''

        def change(session):
            if name in session.keys():
                del session[name]
        self.__change_session(change)

    def __set_session_in_db(self, session):
        session_id = self.__get_session_id()
        pickled_session = pickle.dumps(session)
        self.bucket.set(session_id, pickled_session)
        self.bucket.expire(session_id, self.EXPIRE_SECONDS)

    def __get_session_from_db(self):
        session_id = self.__get_session_id()
        raw_session = self.bucket.get(session_id)

        return self.__to_dict(raw_session)

    def __get_session_id(self):
        session_id = self.handler.get_secure_cookie(self.SESSION_ID_NAME)
        if session_id is None:
            session_id = self.__create_session_id()
        return session_id

    def __create_session_id(self):
        session_id = str(uuid4())
        self.handler.set_secure_cookie(self.SESSION_ID_NAME, session_id,
                                       **self.__cookie_settings())
        return session_id

    def __to_dict(self, raw_session):
        if raw_session is None:
            return {}
        else:
            return pickle.loads(raw_session)

    def __change_session(self, callback):
        session = self.__get_session_from_db()

        callback(session)
        self.__set_session_in_db(session)

    def __cookie_settings(self):
        cookie_settings = self.handler.settings.get('pycket_cookies', {})
        cookie_settings.setdefault('expires', None)
        cookie_settings.setdefault('expires_days', None)
        return cookie_settings


class SessionMixin(object):
    '''
    This mixin must be included in the request handler inheritance list, so that
    the handler can support sessions.

    Example:
    >>> class MyHandler(tornado.web.RequestHandler, SessionMixin):
    ...    def get(self):
    ...        print type(self.session) # SessionManager

    Refer to SessionManager documentation in order to know which methods are
    available.
    '''

    @property
    def session(self):
        '''
        Returns a SessionManager instance
        '''

        return self._get_manager(SessionManager)

    def _get_manager(self, manager_class):
        if not hasattr(self, '__manager'):
            self.__manager = manager_class(self)
        return self.__manager