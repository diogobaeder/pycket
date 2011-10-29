'''
This module contains SessionMixin, which can be used in RequestHandlers, and
SessionManager, which is the real session manager, and is referenced by the
SessionMixin.

It's mandatory that you set the "cookie_secret" in your application settings,
because the session ID is stored in a secure manner. It's also mandatory that
you have a "pycket" dictionary containing at least an "engine" element that
tells which engine you want to use.

Supported engines, for now, are:
- Redis
- Memcache

If you want to change the settings that are passed to the storage client, set a
"storage" dictionary in the "pycket" settings with the intended storage settings
in your Tornado application settings. When you're using Redis, all these
settings are passed to the redis.Redis client, except for the "db_sessions" and
"db_notifications". These settings can contain numbers to change the datasets
used for persistence, if you don't want to use the default numbers.

If you want to change the cookie settings passed to the handler, set a
"cookies" setting in the "pycket" settings with the items you want.
This is also valid for "expires" and "expires_days", which, by default, will be
None, therefore making the sessions expire on browser close, but, if you set one
of them, your custom value will override the default behaviour.
'''

from uuid import uuid4

from pycket.driver import DriverFactory


class SessionManager(object):
    '''
    This is the real class that manages sessions. All session objects are
    persisted in a Redis or Memcache store (depending on your settings).
    After 1 day without changing a session, it's purged from the datastore,
    to avoid it to grow out-of-control.

    When a session is started, a cookie named 'PYCKET_ID' is set, containing the
    encrypted session id of the user. By default, it's cleaned every time the
    user closes the browser.

    The recommendation is to use the manager instance that comes with the
    SessionMixin (using the "session" property of the handler instance), but it
    can be instantiated ad-hoc.
    '''

    SESSION_ID_NAME = 'PYCKET_ID'
    STORAGE_CATEGORY = 'db_sessions'

    driver = None

    def __init__(self, handler):
        '''
        Expects a tornado.web.RequestHandler
        '''

        self.handler = handler
        self.settings = {}
        self.__setup_driver()

    def __setup_driver(self):
        self.__setup_settings()
        storage_settings = self.settings.get('storage', {})
        factory = DriverFactory()
        self.driver = factory.create(self.settings.get('engine'), storage_settings, self.STORAGE_CATEGORY)

    def __setup_settings(self):
        pycket_settings = self.handler.settings.get('pycket')
        if not pycket_settings:
            raise ConfigurationError('The "pycket" configurations are missing')
        engine = pycket_settings.get('engine')
        if not engine:
            raise ConfigurationError('You must define an engine to be used with pycket')
        self.settings = pycket_settings

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

    def delete(self, *names):
        '''
        Deletes the object with "name" from the session, if exists.
        '''

        def change(session):
            keys = session.keys()
            names_in_common = [name for name in names if name in keys]
            for name in names_in_common:
                del session[name]
        self.__change_session(change)
    __delitem__ = delete

    def keys(self):
        session = self.__get_session_from_db()
        return session.keys()

    def iterkeys(self):
        session = self.__get_session_from_db()
        return iter(session)
    __iter__ = iterkeys

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError('%s not found in session' % key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        session = self.__get_session_from_db()
        return key in session

    def __set_session_in_db(self, session):
        session_id = self.__get_session_id()
        self.driver.set(session_id, session)

    def __get_session_from_db(self):
        session_id = self.__get_session_id()
        return self.driver.get(session_id)

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

    def __change_session(self, callback):
        session = self.__get_session_from_db()

        callback(session)
        self.__set_session_in_db(session)

    def __cookie_settings(self):
        cookie_settings = self.settings.get('cookies', {})
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

        return create_mixin(self, '__session_manager', SessionManager)


class ConfigurationError(Exception):
    pass


def create_mixin(context, manager_property, manager_class):
    if not hasattr(context, manager_property):
        setattr(context, manager_property, manager_class(context))
    return getattr(context, manager_property)