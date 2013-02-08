from nose.tools import istest
import redis
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from pycket.driver import RedisDriver
from pycket.session import SessionMixin


class FunctionalTest(AsyncHTTPTestCase):
    dataset = None

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.dataset.flushall()

    def get_app(self):
        if self.dataset is None:
            self.dataset = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_sessions'])

        class SimpleHandler(RequestHandler, SessionMixin):
            def get(self):
                self.session.set('foo', 'bar')
                self.write(self.session.get('foo'))

            def get_secure_cookie(self, *args, **kwargs):
                return 'some-generated-cookie'

        return Application([
            (r'/', SimpleHandler),
        ], **{
            'cookie_secret': 'Python rocks!',
            'pycket': {
                'engine': 'redis',
            }
        })

    @istest
    def works_with_request_handlers(self):
        self.assertEqual(len(self.dataset.keys()), 0)

        response = self.fetch('/')

        self.assertEqual(response.code, 200)
        self.assertIn('bar', response.body)

        self.assertEqual(len(self.dataset.keys()), 1)
