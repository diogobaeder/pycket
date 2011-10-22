from uuid import uuid4

class SessionManager(object):
    SESSION_ID_NAME = 'PYCKET_ID'

    def __init__(self, handler):
        self.handler = handler

    def set(self, name, value):
        session_id = self.__get_session_id()

    def __get_session_id(self):
        session_id = self.handler.get_secure_cookie(self.SESSION_ID_NAME)
        if session_id is None:
            session_id = str(uuid4())
            self.handler.set_secure_cookie(self.SESSION_ID_NAME, session_id, None)


class SessionMixin(object):
    @property
    def session(self):
        if not hasattr(self, '__manager'):
            self.__manager = SessionManager(self)
        return self.__manager