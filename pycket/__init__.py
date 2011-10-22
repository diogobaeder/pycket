#

class SessionManager(object):
    pass


class SessionMixin(object):
    @property
    def session(self):
        if not hasattr(self, '__manager'):
            self.__manager = SessionManager()
        return self.__manager