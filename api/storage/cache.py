import json
from dataclasses import dataclass
from api.config.base import BaseConfig
from typing import Any, Optional
from cachetools import LRUCache
from upstash_redis import Redis


class LRUWrapper:
    def __init__(self, maxsize: float):
        self.cache = LRUCache(maxsize=maxsize)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = value

    def delete(self, key: str) -> None:
        self.cache.pop(key, None)


class UpstashRedisWrapper:
    def __init__(self, url: str, token: str):
        self.redis = Redis(url=url, token=token)

    def get(self, key: str) -> Optional[Any]:
        serialized_value = self.redis.get(key)
        if serialized_value is None:
            return None
        try:
            return json.loads(serialized_value)
        except json.JSONDecodeError:
            return serialized_value

    def set(self, key: str, value: Any, seconds: Optional[int] = None) -> None:
        serialized_value = json.dumps(value, default=str)
        if seconds is not None:
            self.redis.set(key, serialized_value, ex=seconds)
        else:
            self.redis.set(key, serialized_value)

    def delete(self, key: str) -> None:
        self.redis.delete(key)


class RemoteCacheProvider:
    def __init__(self, enabled: bool, wrapper: Optional[UpstashRedisWrapper] = None):
        self.enabled = enabled
        self.wrapper = wrapper

    def get(self, key: str) -> Optional[Any]:
        if self.enabled and self.wrapper:
            return self.wrapper.get(key)
        return None

    def set(self, key: str, value: Any, seconds: Optional[int] = None):
        if self.enabled and self.wrapper:
            self.wrapper.set(key, value, seconds)

    def delete(self, key: str) -> None:
        if self.enabled and self.wrapper:
            self.wrapper.delete(key)


@dataclass
class CacheConfig(BaseConfig):
    lru_size: float = 100.0
    remote_cache_enabled: bool = False
    upstash_redis_rest_url: str = None
    upstash_redis_rest_token: str = None

    @classmethod
    def from_env(cls) -> "CacheConfig":
        return cls(
            lru_size=cls.get_float("LRU_CACHE_SIZE", default=100.0),
            remote_cache_enabled=False,
            upstash_redis_rest_url=cls.get_str("UPSTASH_REDIS_REST_URL"),
            upstash_redis_rest_token=cls.get_str("UPSTASH_REDIS_REST_TOKEN"),
        )

    @classmethod
    def merge(
        cls, base: "CacheConfig", override: Optional["CacheConfig"]
    ) -> "CacheConfig":
        if override is None:
            return base
        return cls(
            lru_size=override.lru_size or base.lru_size,
            remote_cache_enabled=override.remote_cache_enabled
            or base.remote_cache_enabled,
            upstash_redis_rest_url=override.upstash_redis_rest_url
            or base.upstash_redis_rest_url,
            upstash_redis_rest_token=override.upstash_redis_rest_token
            or base.upstash_redis_rest_token,
        )


class MultiTierCacheAdapter:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = CacheConfig.merge(base=CacheConfig.from_env(), override=config)
        self.local = LRUWrapper(maxsize=self.config.lru_size)
        self.remote = RemoteCacheProvider(
            self.config.remote_cache_enabled,
            UpstashRedisWrapper(
                url=self.config.upstash_redis_rest_url,
                token=self.config.upstash_redis_rest_token,
            ),
        )

    def get(self, key):
        value = self.local.get(key)
        if value is not None:
            return value
        value = self.remote.get(key)
        if value is not None:
            self.local.set(key, value)
        return value

    def set(self, key, value):
        self.local.set(key, value)
        self.remote.set(key, value)

    def delete(self, key):
        self.local.delete(key)
        self.remote.delete(key)
