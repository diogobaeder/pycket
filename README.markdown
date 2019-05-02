**DISCONTINUED**

This library is not maintained anymore, hence won't receive any further support.

# pycket
This is a session library, written for use with Redis or Memcached, and Tornado web server.

## Status of the project
[![Build Status](https://secure.travis-ci.org/diogobaeder/pycket.png)](http://travis-ci.org/diogobaeder/pycket)

## License
This software is under BSD 2-Clause License (see LICENSE file)

## Requirements
Non-Python requirements:

* Redis (tested with version 2.4.0) or Memcached (tested with version 1.4.7)

Python requirements (included in setup script)

* Python 2.7, 3.2 or 3.3 (2.6 and 3.1 or lower are not supported, though they might work)
* [Tornado](http://pypi.python.org/pypi/tornado/) (tested with 2.1.1/2.4.1, installable via "tornado" package in PyPI)

Python requirements (not included, because depend on the datastore that you wish to use)

* For Redis: [redis-py](http://pypi.python.org/pypi/redis/) (tested with 2.4.9/2.7.2, installable via "redis" package in PyPI)
* For Memcached on Python 2: [python-memcached](http://pypi.python.org/pypi/python-memcached/) (tested with 1.47/1.48, installable via "python-memcached" package in PyPI)
* For Memcached on Python 3: [python3-memcached](http://pypi.python.org/pypi/python3-memcached/) (tested with 1.44, installable via "python3-memcached" package in PyPI)

## Installing
If you use virtualenv:

```
$ pip install pycket
```

If you don't and your site-packages are shared for all users in your machine:

```
$ sudo pip install pycket
```

If you don't have any idea of what pip is (shame on you!), or can't use it:

```
$ easy_install pycket
```

or, after downloading ([here](http://pypi.python.org/pypi/pycket/)) and unpacking the .tar.gz/.zip package:

```
$ python setup.py install
```

### Development requirements
If you wish to contribute to the project as a developer, just install the requirements file included in the project with pip.

## Examples
You have two ways of using pycket sessions in your application (please refer to the "Settings" section below before starting to use).

The easier way is including the appropriate mixin(s) in the handler's inheritance list, and the "session" member will become available:

```python
from pycket.session import SessionMixin


class MyHandler(tornado.web.RequestHandler, SessionMixin):
    def get(self):
        self.session.set('foo', ['bar', 'baz'])
        foo = self.session.get('foo') # will get back the list ['bar', 'baz']
```

The other way (harder, but less coupled) is to instantiate a SessionManager and passing the handler instance to the initializer:

```python
from pycket.session import SessionManager


class MyHandler(tornado.web.RequestHandler):
    def get(self):
        session = SessionManager(self)
        session.set('foo', ['bar', 'baz'])
        foo = session.get('foo') # will get back the list ['bar', 'baz']
```

For both examples above the session instance is a SessionManager.

SessionManager instances act as a dictionary, so they can retrieve values with a default alternative, like:

```python
session.get("this doesn't exist", "so give me this instead")
```

and they can also get and set values with square-brackets, like:

```python
session['gimme'] = 'Fire!'
print session['gimme'] # 'Fire!'
```

## Settings

### Mandatory settings
pycket understands these types of settings, which must be items in the application's settings:

1. `["pycket"]`: the base settings dictionary for pycket;
1. `["pycket"]["engine"]`: the only mandatory setting. Must be "redis" or "memcached";
1. `["pycket"]["storage"]`: this is a dictionary containing any items that should be repassed to the redis.Redis or
   memcached.Client to be used in the session manager (such as "host", "port", "servers" etc); Notice that for Redis,
   however, that if you want to change the dataset numbers to be used for sessions and notifications, use "db_sessions"
   and "db_notifications", respectively, instead of "db" (they will be converted to the "db" parameter that is passed to
   the Redis client for each manager afterwards);
1. `["pycket"]["cookies"]`: this is a dictionary containing all settings to be repassed to the
   RequestHandler.set_secure_cookie. If they don't contain "expires" or "expires_days" items, they will be set as None,
   which means that the default behaviour for the sessions is to last on browser session. (And deleted as soon as the
   user closes the browser.) Notice that the sessions in the database last for one day, though.

### Optional settings
You can also use these settings.

1. `["pycket"]["storage"]["db_sessions"]` (Redis-only): Dataset to be used for session data;
1. `["pycket"]["storage"]["db_notifications"]` (Redis-only): Dataset to be used for notification data;
1. `["pycket"]["storage"]["max_connections"]` (Redis-only): Maximum connections; If not passed, pycket will use simple
   connections instead of pooling, which may hog your system resources and crash because of the file descriptor limits.

## Examples

### Example using Redis

```python
application = tornado.web.Application([
    (r'/', MainHandler),
], **{
    'pycket': {
        'engine': 'redis',
        'storage': {
            'host': 'localhost',
            'port': 6379,
            'db_sessions': 10,
            'db_notifications': 11,
            'max_connections': 2 ** 31,
        },
        'cookies': {
            'expires_days': 120,
        },
    },
)
```

### Example using Memcached

```python
application = tornado.web.Application([
    (r'/', MainHandler),
], **{
    'pycket': {
        'engine': 'memcached',
        'storage': {
            'servers': ('localhost:11211',)
        },
        'cookies': {
            'expires_days': 120,
        },
    },
)
```

The default Redis dataset numbers for sessions and notifications are, respectively, 0 and 1, and the default Memcached
servers tuple is ("localhost:11211",)

## Notifications
This feature is almost equal to the sessions, but slightly different:

* They have to be used via pycket.notification.NotificationMixin or pycket.notification.NotificationManager;
* The values persisted with them can be retrieved only once, and after this are immediately deleted from the datastore;
* The default Redis dataset used is 1, instead of 0, to avoid conflicts with normal sessions.
* Unfortunately, for Memcached, the notifications are saved in the same datastore as the sessions, because I still didn't find a way keep them in a separate datastore.

## Connection pooling (Redis)
As noted earlier, you can imply the usage of connection pools by using the `["pycket"]["storage"]["max_connections"]` 
setting. If you use it, pycket will create two connection pools - one for the sessions, and one for the notifications -.

## Author
This module was developed by Diogo Baeder (*/diogobaeder), who is an absolute Python lover, and is currently in love with event-driven programming and ArchLinux.
