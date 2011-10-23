'''
This module contains SessionMixin, which can be used in RequestHandlers, and
SessionManager, which is the real session manager, and is referenced by the
SessionMixin.
If you want to change the settings that are passed to the Redis client, set a
"pycket_redis" dictionary with the intended Redis settings in your Tornado
application settings. All these settings are passed to the redis.Redis client
(except for the "db" parameter, which is always set to "pycket_sessions")
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
    SESSION_DB = 'pycket_sessions'
    EXPIRE_SECONDS = 24 * 60 * 60

    def __init__(self, handler):
        '''
        Expects a tornado.web.RequestHandler
        '''

        self.handler = handler
        redis_settings = handler.settings.get('pycket_redis', {})
        redis_settings['db'] = self.SESSION_DB
        self.client = redis.Redis(**redis_settings)

    def set(self, name, value):
        '''
        Sets a value for "name". It may be any pickable (see "pickle" module
        documentation) object.
        '''

        def change(session):
            session[name] = value
        self.__change_session(change)

    def get(self, name):
        '''
        Gets the object for "name", or None if there's no such object.
        '''

        session = self.__get_session_from_db()

        return session.get(name)

    def delete(self, name):
        '''
        Deletes the object with "name" from the session.
        '''

        def change(session):
            del session[name]
        self.__change_session(change)

    def __set_session_in_db(self, session):
        session_id = self.__get_session_id()
        pickled_session = pickle.dumps(session)
        self.client.set(session_id, pickled_session)
        self.client.expire(session_id, self.EXPIRE_SECONDS)

    def __get_session_from_db(self):
        session_id = self.__get_session_id()
        raw_session = self.client.get(session_id)

        return self.__to_dict(raw_session)

    def __get_session_id(self):
        session_id = self.handler.get_secure_cookie(self.SESSION_ID_NAME)
        if session_id is None:
            session_id = self.__create_session_id()
        return session_id

    def __create_session_id(self):
        session_id = str(uuid4())
        self.handler.set_secure_cookie(self.SESSION_ID_NAME, session_id, None)
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

        if not hasattr(self, '__manager'):
            self.__manager = SessionManager(self)
        return self.__manager