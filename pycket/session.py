import pickle
from uuid import uuid4

import redis

class SessionManager(object):
    SESSION_ID_NAME = 'PYCKET_ID'
    SESSION_DB = 'pycket_sessions'

    def __init__(self, handler):
        self.handler = handler
        self.client = redis.Redis(db=self.SESSION_DB)

    def set(self, name, value):
        def change(session):
            session[name] = value
        self.__change_session(change)

    def get(self, name):
        session = self.__get_session_from_db()

        return session.get(name)

    def delete(self, name):
        def change(session):
            del session[name]
        self.__change_session(change)

    def __set_session_in_db(self, session):
        session_id = self.__get_session_id()
        pickled_session = pickle.dumps(session)
        self.client.set(session_id, pickled_session)

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
    @property
    def session(self):
        if not hasattr(self, '__manager'):
            self.__manager = SessionManager(self)
        return self.__manager