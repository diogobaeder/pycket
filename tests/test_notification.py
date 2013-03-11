import pickle
from unittest import TestCase

from nose.tools import istest
import redis

from pycket.driver import RedisDriver
from pycket.session import SessionMixin
from pycket.notification import NotificationManager, NotificationMixin


class RedisTestCase(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            self.client = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_notifications'])
        self.client.flushall()


class NotificationMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(NotificationMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

        self.assertIsInstance(StubHandler().notifications, NotificationManager)


class NotificationManagerTest(RedisTestCase):
    @istest
    def persists_in_a_different_name_from_session_manager(self):
        self.assertNotEqual(RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_notifications'], RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_sessions'])

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

        self.assertEqual(list(notifications.keys()), ['foo'])

        manager.get('foo')

        raw_notifications = self.client.get(handler.session_id)
        notifications = pickle.loads(raw_notifications)

        self.assertEqual(list(notifications.keys()), [])

    @istest
    def gets_default_value_if_provided_and_not_in_client(self):
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
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

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
            'pycket': {
                'engine': 'redis',
                'storage': {
                    'db_sessions': 10,
                    'db_notifications': 11,
                }
            }
        }
        manager = NotificationManager(handler)
        manager.set('foo', 'bar')
        self.assertEqual(manager.driver.client.connection_pool._available_connections[0].db, 11)


class StubHandler(object):
    session_id = 'session-id'

    def __init__(self, settings=None):
        default_settings = {
            'pycket': {
                'engine': 'redis',
            }
        }
        self.settings = settings if settings is not None else default_settings

    def get_secure_cookie(self, name):
        return self.session_id
