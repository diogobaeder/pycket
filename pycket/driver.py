from copy import copy
import pickle

import redis


class RedisDriver(object):
    EXPIRE_SECONDS = 24 * 60 * 60
    DEFAULT_STORAGE_IDENTIFIERS = {
        'db_sessions': 0,
        'db_notifications': 1,
    }

    dataset = None

    def __init__(self, settings):
        self.settings = settings

    def set(self, session_id, session):
        pickled_session = pickle.dumps(session)
        self.__setup_dataset()
        self.dataset.set(session_id, pickled_session)
        self.dataset.expire(session_id, self.EXPIRE_SECONDS)

    def get(self, session_id):
        self.__setup_dataset()
        raw_session = self.dataset.get(session_id)

        return self.__to_dict(raw_session)

    def __to_dict(self, raw_session):
        if raw_session is None:
            return {}
        else:
            return pickle.loads(raw_session)

    def __setup_dataset(self):
        if self.dataset is None:
            self.dataset = redis.Redis(**self.settings)


class DriverFactory(object):
    STORAGE_CATEGORIES = ('db_sessions', 'db_notifications')

    def create(self, name, storage_settings, storage_category):
        return self.__create_redis(storage_settings, storage_category)

    def __create_redis(self, storage_settings, storage_category):
        storage_settings = copy(storage_settings)
        default_storage_identifier = RedisDriver.DEFAULT_STORAGE_IDENTIFIERS[storage_category]
        storage_settings['db'] = storage_settings.get(storage_category, default_storage_identifier)
        for storage_category in self.STORAGE_CATEGORIES:
            if storage_category in storage_settings.keys():
                del storage_settings[storage_category]

        return RedisDriver(storage_settings)