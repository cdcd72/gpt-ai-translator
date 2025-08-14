from dataclasses import dataclass
from config.base import BaseConfig
from typing import Optional
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


@dataclass
class CacheConfig(BaseConfig):
    lru_size: float

    @classmethod
    def from_env(cls) -> "CacheConfig":
        return cls(lru_size=cls.get_float("LRU_CACHE_SIZE", default=100.0))


class MultiTierCacheAdapter:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig.from_env()
        self.local = LRUWrapper(maxsize=self.config.lru_size)
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
