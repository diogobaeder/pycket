from copy import copy
import pickle

import redis


class RedisDriver(object):
    EXPIRE_SECONDS = 24 * 60 * 60

    dataset = None

    def __init__(self, manager, settings):
        self.manager = manager
        self.settings = settings

    def load(self, dataset):
        self.dataset = dataset

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