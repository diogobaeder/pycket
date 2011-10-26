import pickle
import time
from unittest import TestCase

from nose.tools import istest
import redis

from pycket.session import SessionManager, SessionMixin
from pycket.notification import NotificationManager, NotificationMixin


class RedisTestCase(TestCase):
    dataset = None

    def setUp(self):
        if self.dataset is None:
            self.dataset = redis.Redis(db=self.DB)
        self.dataset.flushall()


class NotificationMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(NotificationMixin):
            settings = {}

        self.assertIsInstance(StubHandler().notifications, NotificationManager)


class NotificationManagerTest(RedisTestCase):
    DB = NotificationManager.DB

    @istest
    def persists_in_a_different_name_from_session_manager(self):
        self.assertNotEqual(NotificationManager.DB, SessionManager.DB)

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

        raw_notifications = self.dataset.get(handler.session_id)
        notifications = pickle.loads(raw_notifications)

        self.assertEqual(notifications.keys(), ['foo'])

        manager.get('foo')

        raw_notifications = self.dataset.get(handler.session_id)
        notifications = pickle.loads(raw_notifications)

        self.assertEqual(notifications.keys(), [])

    @istest
    def gets_default_value_if_provided_and_not_in_dataset(self):
        handler = StubHandler()
        manager = NotificationManager(handler)

        value = manager.get('foo', 'Default')

        self.assertEqual(value, 'Default')

    @istest
    def sets_object_with_dict_key(self):
        handler = StubHandler()
        manager = NotificationManager(handler)

        manager['foo'] = 'bar'

        self.assertEqual(manager['foo'], 'bar')

    @istest
    def doesnt_conflict_with_sessions(self):
        test_case = self

        class StubHandler(SessionMixin, NotificationMixin):
            session_id = 'session-id'
            settings = {}

            def get_secure_cookie(self, name):
                return self.session_id

            def test(self):
                self.session.set('foo', 'foo-session')
                self.notifications.set('foo', 'foo-notification')

                test_case.assertEqual(self.session.get('foo'), 'foo-session')
                test_case.assertEqual(self.notifications.get('foo'), 'foo-notification')
                test_case.assertIsNone(self.notifications.get('foo'))

        handler = StubHandler()

        handler.test()

    @istest
    def uses_custom_notifications_database_if_provided(self):
        handler = StubHandler()
        handler.settings = {
            'pycket_redis': {
                'db_sessions': 10,
                'db_notifications': 11,
            }
        }
        manager = NotificationManager(handler)
        manager.set('foo', 'bar')
        self.assertEqual(manager.driver.dataset.connection_pool._available_connections[0].db, 11)


class StubHandler(object):
    session_id = 'session-id'

    def __init__(self, settings=None):
        self.settings = settings if settings is not None else {}

    def get_secure_cookie(self, name):
        return self.session_id
