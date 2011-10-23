'''
This module is the same as the sessions module, except that NotificationMixin
sets a "notifications" property instead a "session" one, and that the
NotificationManager ("notifications") gets an object only once, and deletes it
from the database after retrieving
'''

from pycket.session import SessionManager, SessionMixin


class NotificationManager(SessionManager):
    DB_NAME = 'pycket_notifications'

    def get(self, name):
        '''
        Retrieves the object with "name", like with SessionManager.get(), but
        removes the object from the database after retrieval, so that it can be
        retrieved only once
        '''
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