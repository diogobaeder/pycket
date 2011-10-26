import pickle

import redis


class RedisDriver(object):
    dataset = None

    def __init__(self, manager):
        self.manager = manager

    def load(self, dataset):
        self.dataset = dataset

    def set(self, session_id, pickled_session):
        self.dataset.set(session_id, pickled_session)
        self.dataset.expire(session_id, self.manager.EXPIRE_SECONDS)

    def get(self, session_id):
        raw_session = self.dataset.get(session_id)

        return self.__to_dict(raw_session)

    def __to_dict(self, raw_session):
        if raw_session is None:
            return {}
        else:
            return pickle.loads(raw_session)