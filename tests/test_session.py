import pickle
import time
from unittest import skip, skipIf, TestCase

from nose.tools import istest, raises
import redis

from pycket.driver import RedisDriver
from pycket.session import SessionManager, SessionMixin


skip_slow_tests = True


class SessionMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(SessionMixin):
            settings = {}

        self.assertIsInstance(StubHandler().session, SessionManager)


class RedisTestCase(TestCase):
    dataset = None

    def setUp(self):
        if self.dataset is None:
            self.dataset = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_sessions'])
        self.dataset.flushall()


class SessionManagerTest(RedisTestCase):
    @istest
    def sets_session_id_on_cookies(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {}
            def get_secure_cookie(self, name):
                test_case.assertEqual(name, 'PYCKET_ID')
                self.cookie_set = True
                return None

            def set_secure_cookie(self, name, value, expires_days, expires):
                test_case.assertEqual(name, 'PYCKET_ID')
                test_case.assertIsInstance(value, basestring)
                test_case.assertGreater(len(value), 0)
                self.cookie_retrieved = True

        handler = StubHandler()
        session_manager = SessionManager(handler)
        session_manager.set('some-object', 'Some object')

        self.assertTrue(handler.cookie_retrieved)
        self.assertTrue(handler.cookie_set)

    @istest
    def does_not_set_session_id_if_already_exists(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {}
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

        raw_session = self.dataset.get(handler.session_id)
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

        raw_session = self.dataset.get(handler.session_id)
        session = pickle.loads(raw_session)

        self.assertEqual(session.keys(), ['some-object2'])

    @istest
    def starts_with_1_day_to_expire_in_database(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        one_day = 24 * 60 * 60

        self.assertEqual(manager.EXPIRE_SECONDS, one_day)

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
        manager.EXPIRE_SECONDS = 1

        manager.set('foo', 'bar')

        time.sleep(manager.EXPIRE_SECONDS + 1)

        self.assertIsNone(manager.get('foo'))

    @istest
    def repasses_pycket_redis_settings_to_client(self):
        test_case = self
        settings = {'was_retrieved': False}

        class StubSettings(dict):
            def get(self, name, default):
                test_case.assertEqual(name, 'pycket_redis')
                test_case.assertEqual(default, {})
                settings['was_retrieved'] = True
                return default

        handler = StubHandler(StubSettings())
        manager = SessionManager(handler)
        manager.get('some value to setup the dataset')

        self.assertTrue(settings['was_retrieved'])

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
    def gets_default_value_if_provided_and_not_in_dataset(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        value = manager.get('foo', 'Default')

        self.assertEqual(value, 'Default')

    @istest
    def sets_session_id_to_last_a_browser_session_as_default(self):
        test_case = self

        class StubHandler(SessionMixin):
            settings = {}
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
                'pycket_cookies': {
                    'foo': 'bar',
                }
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
                'pycket_cookies': {
                    'expires': 'St. Neversday',
                }
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
                'pycket_cookies': {
                    'expires_days': 'St. Neversday',
                }
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
            'pycket_redis': {
                'db_sessions': 10,
                'db_notifications': 11,
            }
        }
        manager = SessionManager(handler)
        manager.set('foo', 'bar')
        self.assertEqual(manager.driver.dataset.connection_pool._available_connections[0].db, 10)

    @istest
    def deletes_multiple_session_objects_at_once(self):
        handler = StubHandler()
        manager = SessionManager(handler)

        manager.set('some-object', {'foo': 'bar'})
        manager.set('some-object2', {'foo2': 'bar2'})
        manager.delete('some-object', 'some-object2')

        raw_session = self.dataset.get(handler.session_id)
        session = pickle.loads(raw_session)

        self.assertEqual(session.keys(), [])

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

        self.assertListEqual(manager.keys(), ['foo', 'bar'])

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
        self.settings = settings if settings is not None else {}

    def get_secure_cookie(self, name):
        return self.session_id
