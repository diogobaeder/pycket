import pickle

from nose.tools import istest
import redis
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from pycket.driver import RedisDriver
from pycket.notification import NotificationMixin
from pycket.session import SessionMixin


class FunctionalTest(AsyncHTTPTestCase):
    session_dataset = None
    notification_dataset = None

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.session_dataset.flushall()
        self.notification_dataset.flushall()

    def get_app(self):
        if self.session_dataset is None or self.notification_dataset is None:
            self.session_dataset = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_sessions'])
            self.notification_dataset = redis.Redis(db=RedisDriver.DEFAULT_STORAGE_IDENTIFIERS['db_notifications'])

        class SimpleHandler(RequestHandler, SessionMixin, NotificationMixin):
            def get(self):
                self.session.set('foo', 'bar')
                self.notifications.set('foo', 'bar2')
                self.write('%s-%s' % (self.session.get('foo'), self.notifications.get('foo')))

            def get_secure_cookie(self, *args, **kwargs):
                return 'some-generated-cookie'

        return Application([
            (r'/', SimpleHandler),
        ], **{
            'cookie_secret': 'Python rocks!',
            'pycket': {
                'engine': 'redis',
                'storage': {
                    'max_connections': 10,
                },
            }
        })

    @istest
    def works_with_request_handlers(self):
        self.assertEqual(len(self.session_dataset.keys()), 0)

        response = self.fetch('/')

        self.assertEqual(response.code, 200)
        self.assertIn('bar-bar2', str(response.body))

        session_data = pickle.loads(self.session_dataset['some-generated-cookie'])
        notification_data = pickle.loads(self.notification_dataset['some-generated-cookie'])
        self.assertEqual(session_data, {'foo': 'bar'})
        self.assertEqual(notification_data, {})
