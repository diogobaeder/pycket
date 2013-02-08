import pickle
from unittest import TestCase

from nose.tools import istest, raises
import redis

from pycket.driver import DriverFactory, MemcachedDriver, RedisDriver


class RedisTestCase(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            self.client = redis.Redis(db=0)
        self.client.flushall()


class RedisDriverTest(RedisTestCase):
    @istest
    def inserts_pickable_object_into_session(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        driver.set('session-id', foo)

        result = self.client.get('session-id')

        self.assertEqual(pickle.loads(result), foo)

    @istest
    def retrieves_a_pickled_object_from_session(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        self.client.set('session-id', pickle.dumps(foo))

        result = driver.get('session-id')

        self.assertEqual(result, foo)

    @istest
    def makes_session_expire_in_one_day_in_the_client(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        test_case = self

        class StubClient(object):
            def set(self, session_id, pickled_session):
                pass

            def expire(self, session_id, expiration):
                test_case.assertEqual(expiration, RedisDriver.EXPIRE_SECONDS)

        driver.client = StubClient()

        driver.set('session-id', foo)

    @istest
    def starts_with_1_day_to_expire_in_database(self):
        driver = RedisDriver(dict(db=0))

        one_day = 24 * 60 * 60

        self.assertEqual(driver.EXPIRE_SECONDS, one_day)


class MemcachedTestCase(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            import memcache
            self.client = memcache.Client(servers=('localhost:11211',))
        self.client.flush_all()


class MemcachedDriverTest(MemcachedTestCase):
    @istest
    def inserts_pickable_object_into_session(self):
        driver = MemcachedDriver({
            'servers': ('localhost:11211',)
        })

        foo = dict(foo='bar')

        driver.set('session-id', foo)

        result = self.client.get('session-id')

        self.assertEqual(pickle.loads(result), foo)

    @istest
    def retrieves_a_pickled_object_from_session(self):
        driver = MemcachedDriver({
            'servers': ('localhost:11211',)
        })

        foo = dict(foo='bar')

        self.client.set('session-id', pickle.dumps(foo))

        result = driver.get('session-id')

        self.assertEqual(result, foo)

    @istest
    def makes_session_expire_in_one_day_in_the_client(self):
        driver = MemcachedDriver({
            'servers': ('localhost:11211',)
        })

        foo = dict(foo='bar')

        test_case = self

        class StubClient(object):
            def set(self, session_id, pickled_session, expiration):
                test_case.assertEqual(expiration, MemcachedDriver.EXPIRE_SECONDS)

        driver.client = StubClient()

        driver.set('session-id', foo)

    @istest
    @raises(OverflowError)
    def fails_to_load_if_storage_settings_contain_wrong_host(self):
        driver = MemcachedDriver({
            'servers': ('255.255.255.255:99999',)
        })

        driver.set('session-id', 'foo')

    @istest
    def starts_with_1_day_to_expire_in_database(self):
        driver = MemcachedDriver({
            'servers': ('localhost:11211',)
        })

        one_day = 24 * 60 * 60

        self.assertEqual(driver.EXPIRE_SECONDS, one_day)


class DriverFactoryTest(TestCase):
    @istest
    def creates_instance_for_redis_session(self):
        factory = DriverFactory()

        instance = factory.create('redis', storage_settings={}, storage_category='db_sessions')

        self.assertIsInstance(instance, RedisDriver)

        instance.get('client-is-lazy-loaded')

        self.assertEqual(instance.client.connection_pool._available_connections[0].db, 0)

    @istest
    def creates_instance_for_memcached_session(self):
        factory = DriverFactory()

        instance = factory.create('memcached', storage_settings={}, storage_category='db_sessions')

        self.assertIsInstance(instance, MemcachedDriver)

        instance.get('client-is-lazy-loaded')

        self.assertIsNotNone(instance.client.get_stats())

    @istest
    @raises(ValueError)
    def cannot_create_a_driver_for_not_supported_engine(self):
        factory = DriverFactory()

        factory.create('cassete-tape', storage_settings={}, storage_category='db_sessions')
