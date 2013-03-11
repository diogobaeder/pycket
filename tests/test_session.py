import pickle
import time
from unittest import skipIf, TestCase

from nose.tools import istest, raises
import redis

from pycket.driver import MemcachedDriver, RedisDriver
from pycket.session import ConfigurationError, SessionManager, SessionMixin


skip_slow_tests = False


class SessionMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

        self.assertIsInstance(StubHandler().session, SessionManager)

    @istest
    @raises(ConfigurationError)
    def cannot_start_driver_without_pycket_settings(self):
        class StubHandler(SessionMixin):
            settings = {}

        StubHandler().session.get('something')

    @istest
    @raises(ConfigurationError)
    def cannot_start_driver_without_pycket_engine(self):
        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'not-an-engine': 'something-useless',
                }
            }

        StubHandler().session.get('something')

    @istest
    def creates_session_for_redis(self):
        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

        self.assertIsInstance(StubHandler().session.driver, RedisDriver)

    @istest
    def creates_session_for_memcached(self):
        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'memcached',
                }
            }

        self.assertIsInstance(StubHandler().session.driver, MemcachedDriver)


class RedisTestCase(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            self.client = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_sessions'])
        self.client.flushall()


class SessionManagerTest(RedisTestCase):
    @istest
    def sets_session_id_on_cookies(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

            def get_secure_cookie(self, name):
                test_case.assertEqual(name, 'PYCKET_ID')
                self.cookie_set = True
                return None

            def set_secure_cookie(self, name, value, expires_days, expires):
                test_case.assertEqual(name, 'PYCKET_ID')
                test_case.assertIsInstance(value, str)
                test_case.assertGreater(len(value), 0)
                self.cookie_retrieved = True

        handler = StubHandler()
        session_manager = SessionManager(handler)
        session_manager.set('some-object', 'Some object')

        self.assertTrue(handler.cookie_retrieved)
        self.assertTrue(handler.cookie_set)

    @istest
    def does_not_set_session_id_if_already_exists(self):
        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

            def get_secure_cookie(self, name):
                self.cookie_retrieved = True
                return 'some-id'

        handler = StubHandler()
        manager = SessionManager(handler)
        manager.set('some-object', 'Some object')

        self.assertTrue(handler.cookie_retrieved)

    @istest
    def saves_session_object_on_redis_with_same_session_id_as_cookie(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})

        raw_session = self.client.get(handler.session_id)
        session = pickle.loads(raw_session)

        self.assertEqual(session['some-object']['foo'], 'bar')

    @istest
    def retrieves_session_with_same_data_as_saved(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})

        self.assertEqual(manager.get('some-object')['foo'], 'bar')

    @istest
    def keeps_previous_items_when_setting_new_ones(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})
        manager.set('some-object2', {'foo2': 'bar2'})

        self.assertEqual(manager.get('some-object')['foo'], 'bar')
        self.assertEqual(manager.get('some-object2')['foo2'], 'bar2')

    @istest
    def retrieves_none_if_session_object_not_previously_set(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        self.assertIsNone(manager.get('unexistant-object'))

    @istest
    def deletes_objects_from_session(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})
        manager.set('some-object2', {'foo2': 'bar2'})
        manager.delete('some-object')

        raw_session = self.client.get(handler.session_id)
        session = pickle.loads(raw_session)

        self.assertEqual(list(session.keys()), ['some-object2'])

    @istest
    @skipIf(skip_slow_tests, 'This test is too slow')
    def still_retrieves_object_if_not_passed_from_expiration(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('foo', 'bar')

        time.sleep(1)

        self.assertEqual(manager.get('foo'), 'bar')

    @istest
    @skipIf(skip_slow_tests, 'This test is too slow')
    def cannot_retrieve_object_if_passed_from_expiration(self):
        handler = StubHandler()
        manager = SessionManager(handler)
        manager.driver.EXPIRE_SECONDS = 1

        manager.set('foo', 'bar')

        time.sleep(manager.driver.EXPIRE_SECONDS + 1)

        self.assertIsNone(manager.get('foo'))

    @istest
    def retrieves_object_with_dict_key(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('foo', 'bar')

        self.assertEqual(manager['foo'], 'bar')

    @istest
    @raises(KeyError)
    def raises_key_error_if_object_doesnt_exist(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager['foo']

    @istest
    def sets_object_with_dict_key(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager['foo'] = 'bar'

        self.assertEqual(manager['foo'], 'bar')

    @istest
    def gets_default_value_if_provided_and_not_in_client(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        value = manager.get('foo', 'Default')

        self.assertEqual(value, 'Default')

    @istest
    def sets_session_id_to_last_a_browser_session_as_default(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                }
            }

            def get_secure_cookie(self, name):
                return None

            def set_secure_cookie(self, name, value, expires_days, expires):
                test_case.assertIsNone(expires_days)
                test_case.assertIsNone(expires)

        handler = StubHandler()
        manager = SessionManager(handler)
        manager.set('some-object', 'Some object')

    @istest
    def repasses_cookies_options(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                    'cookies': {
                        'foo': 'bar',
                    }
                },
            }

            def get_secure_cookie(self, name):
                return None

            def set_secure_cookie(self, *args, **kwargs):
                test_case.assertEqual(kwargs['foo'], 'bar')

        handler = StubHandler()
        manager = SessionManager(handler)
        manager.set('some-object', 'Some object')

    @istest
    def uses_custom_expires_if_provided(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                    'cookies': {
                        'expires': 'St. Neversday',
                    }
                },
            }

            def get_secure_cookie(self, name):
                return None

            def set_secure_cookie(self, *args, **kwargs):
                test_case.assertEqual(kwargs['expires'], 'St. Neversday')

        handler = StubHandler()
        manager = SessionManager(handler)
        manager.set('some-object', 'Some object')

    @istest
    def uses_custom_expires_days_if_provided(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {
                'pycket': {
                    'engine': 'redis',
                    'cookies': {
                        'expires_days': 'St. Neversday',
                    }
                },
            }

            def get_secure_cookie(self, name):
                return None

            def set_secure_cookie(self, *args, **kwargs):
                test_case.assertEqual(kwargs['expires_days'], 'St. Neversday')

        handler = StubHandler()
        manager = SessionManager(handler)
        manager.set('some-object', 'Some object')

    @istest
    def uses_custom_sessions_database_if_provided(self):
        handler = StubHandler()
        handler.settings = {
            'pycket': {
                'engine': 'redis',
                'storage': {
                    'db_sessions': 10,
                    'db_notifications': 11,
                }
            },
        }
        manager = SessionManager(handler)
        manager.set('foo', 'bar')
        self.assertEqual(manager.driver.client.connection_pool._available_connections[0].db, 10)

    @istest
    def deletes_multiple_session_objects_at_once(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})
        manager.set('some-object2', {'foo2': 'bar2'})
        manager.delete('some-object', 'some-object2')

        raw_session = self.client.get(handler.session_id)
        session = pickle.loads(raw_session)

        self.assertEqual(list(session.keys()), [])

    @istest
    def deletes_item_using_command(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})

        del manager['some-object']

        self.assertIsNone(manager.get('some-object'))

    @istest
    def verifies_if_a_session_exist(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        self.assertFalse('foo' in manager)

        manager['foo'] = 'bar'

        self.assertTrue('foo' in manager)

    @istest
    def gets_all_available_keys_from_session(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('foo', 'FOO')
        manager.set('bar', 'BAR')

        self.assertListEqual(sorted(manager.keys()), sorted(['foo', 'bar']))

    @istest
    def iterates_with_method_over_keys(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('foo', 'FOO')
        manager.set('bar', 'BAR')

        iterations = 0

        for key in manager.iterkeys():
            self.assertTrue(key in manager)
            iterations += 1

        self.assertEqual(iterations, 2)

    @istest
    def iterates_without_method_over_keys(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('foo', 'FOO')
        manager.set('bar', 'BAR')

        iterations = 0

        for key in manager:
            self.assertTrue(key in manager)
            iterations += 1

        self.assertEqual(iterations, 2)


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
