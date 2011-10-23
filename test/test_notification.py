import pickle
import time
from unittest import TestCase

from nose.tools import istest
import redis

from pycket.session import SessionManager, SessionMixin
from pycket.notification import NotificationManager, NotificationMixin


class RedisTestCase(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            self.client = redis.Redis(db=self.DB_NAME)
        self.client.flushdb()


class NotificationMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(NotificationMixin):
            settings = {}

        self.assertIsInstance(StubHandler().notification, NotificationManager)


class NotificationManagerTest(RedisTestCase):
    DB_NAME = NotificationManager.DB_NAME

    @istest
    def persists_in_a_different_name_from_session_manager(self):
        self.assertNotEqual(NotificationManager.DB_NAME, SessionManager.DB_NAME)

    @istest
    def gets_a_notification_only_once(self):
        handler = StubHandler()
        manager = NotificationManager(handler)

        manager.set('foo', 'bar')

        self.assertEqual(manager.get('foo'), 'bar')
        self.assertIsNone(manager.get('foo'))

    @istest
    def removes_notification_from_database_after_retrieval(self):
        handler = StubHandler()
        manager = NotificationManager(handler)

        manager.set('foo', 'bar')

        raw_notifications = self.client.get(handler.session_id)
        notifications = pickle.loads(raw_notifications)

        self.assertEqual(notifications.keys(), ['foo'])

        manager.get('foo')

        raw_notifications = self.client.get(handler.session_id)
        notifications = pickle.loads(raw_notifications)

        self.assertEqual(notifications.keys(), [])


class StubHandler(SessionMixin):
    session_id = 'session-id'
    settings = {}

    def get_secure_cookie(self, name):
        return self.session_id
