'''
This module is the same as the sessions module, except that:
1. NotificationMixin sets a "notifications" property instead a "session" one,
and that the NotificationManager ("notifications") gets an object only once, and
deletes it from the database after retrieving;
2. The objects are stored in db 1 (for default) instead of 0 to avoid conflicts
with sessions. (You can change this setting with the "db_notifications" setting
in the "storage" setting.)
'''

from pycket.session import create_mixin, SessionManager


class NotificationManager(SessionManager):
    STORAGE_CATEGORY = 'db_notifications'

    def get(self, name, default=None):
        '''
        Retrieves the object with "name", like with SessionManager.get(), but
        removes the object from the database after retrieval, so that it can be
        retrieved only once
        '''

        session_object = super(NotificationManager, self).get(name, default)
        if session_object is not None:
            self.delete(name)
        return session_object


class NotificationMixin(object):
    @property
    def notifications(self):
        '''
        Returns a NotificationManager instance
        '''

        return create_mixin(self, '__notification_manager', NotificationManager)
