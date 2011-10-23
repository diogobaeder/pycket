import pickle
from unittest import TestCase

from nose.tools import istest
import redis

from pycket.session import SessionManager, SessionMixin


class SessionMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(SessionMixin):
            pass

        self.assertIsInstance(StubHandler().session, SessionManager)



class SessionManagerTest(TestCase):
    client = None

    def setUp(self):
        if self.client is None:
            self.client = redis.Redis(db=SessionManager.SESSION_DB)
        self.client.flushdb()

    @istest
    def sets_session_id_on_cookies(self):
        test_case = self

        class StubHandler(SessionMixin):
            def get_secure_cookie(self, name):
                test_case.assertEqual(name, 'PYCKET_ID')
                self.cookie_set = True
                return None

            def set_secure_cookie(self, name, value, expire_days):
                test_case.assertEqual(name, 'PYCKET_ID')
                test_case.assertIsInstance(value, basestring)
                test_case.assertGreater(len(value), 0)
                test_case.assertEqual(expire_days, None)
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
            def get_secure_cookie(self, name):
                self.cookie_retrieved = True
                return 'some-id'

        handler = StubHandler()
        session_manager = SessionManager(handler)
        session_manager.set('some-object', 'Some object')

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


class StubHandler(SessionMixin):
    session_id = 'session-id'

    def get_secure_cookie(self, name):
        return self.session_id
