import pickle
from unittest import TestCase

from nose.tools import istest, raises
import redis

from pycket.driver import DriverFactory, RedisDriver


class RedisTestCase(TestCase):
    dataset = None

    def setUp(self):
        if self.dataset is None:
            self.dataset = redis.Redis(db=0)
        self.dataset.flushall()


class RedisDriverTest(RedisTestCase):
    @istest
    def inserts_pickable_object_into_session(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        driver.set('session-id', foo)

        result = self.dataset.get('session-id')

        self.assertEqual(pickle.loads(result), foo)

    @istest
    def retrieves_a_pickled_object_from_session(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        self.dataset.set('session-id', pickle.dumps(foo))

        result = driver.get('session-id')

        self.assertEqual(result, foo)

    @istest
    def makes_session_expire_in_one_day_in_the_dataset(self):
        driver = RedisDriver(dict(db=0))

        foo = dict(foo='bar')

        test_case = self

        class StubClient(object):
            def set(self, session_id, pickled_session):
                pass

            def expire(self, session_id, expiration):
                test_case.assertEqual(expiration, RedisDriver.EXPIRE_SECONDS)

        driver.dataset = StubClient()

        driver.set('session-id', foo)


class DriverFactoryTest(TestCase):
    @istest
    def creates_instance_for_redis_session(self):
        factory = DriverFactory()

        instance = factory.create('redis', storage_settings={}, storage_category='db_sessions')

        self.assertIsInstance(instance, RedisDriver)

        instance.get('dataset-is-lazy-loaded')

        self.assertEqual(instance.dataset.connection_pool._available_connections[0].db, 0)