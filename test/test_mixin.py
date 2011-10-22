from unittest import TestCase

from nose.tools import istest

from pycket import SessionManager, SessionMixin


class SessionMixinTest(TestCase):
    @istest
    def starts_handler_with_session_manager(self):
        class StubHandler(SessionMixin):
            pass

        self.assertIsInstance(StubHandler().session, SessionManager)