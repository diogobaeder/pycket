from pycket.session import SessionManager, SessionMixin


class NotificationManager(SessionManager):
    DB_NAME = 'pycket_notifications'

    def get(self, name):
        session_object = super(NotificationManager, self).get(name)
        if session_object is not None:
            self.delete(name)
        return session_object


class NotificationMixin(SessionMixin):
    MANAGER_CLASS = NotificationManager

    @property
    def notifications(self):
        '''
        Returns a NotificationManager instance
        '''

        return self._get_manager()