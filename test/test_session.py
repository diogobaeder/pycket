from unittest import TestCase

from nose.tools import istest

from pycket.session import SessionManager, SessionMixin


class SessionMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(SessionMixin):
            pass

        self.assertIsInstance(StubHandler().session, SessionManager)



class SessionManagerTest(TestCase):
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


class StubHandler(SessionMixin):
    session_id = 'session-id'

    def get_secure_cookie(self, name):
        return self.session_id
