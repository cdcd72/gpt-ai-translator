import os

from cachetools import LRUCache


class LRUWrapper:
    def __init__(self, maxsize):
        self.cache = LRUCache(maxsize=maxsize)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        self.cache.pop(key, None)


class MultiTierCacheAdapter:
    def __init__(self):
        self.local = LRUWrapper(maxsize=float(os.getenv("LRU_CACHE_SIZE", "100")))
        # self.remote = remote_cache

    def get(self, key):
        value = self.local.get(key)
        if value is not None:
            return value
        # value = self.remote.get(key)
        # if value is not None:
        #     self.local.set(key, value)
        return value

    def set(self, key, value):
        self.local.set(key, value)
        # self.remote.set(key, value)

    def delete(self, key):
        self.local.delete(key)
        # self.remote.delete(key)
