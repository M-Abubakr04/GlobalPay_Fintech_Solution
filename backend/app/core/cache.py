import json
from typing import Any

from app.core.config import settings

try:
    from redis import Redis
    from redis.exceptions import RedisError
except ImportError:  # Allows unit tests/IDE inspection before optional dependencies are installed.
    class RedisError(Exception):
        pass

    class Redis:  # type: ignore[no-redef]
        @classmethod
        def from_url(cls, *_args, **_kwargs):
            return cls()

        def get(self, _key):
            raise RedisError("Redis package is not installed")

        def setex(self, *_args, **_kwargs):
            raise RedisError("Redis package is not installed")

        def ping(self):
            raise RedisError("Redis package is not installed")

        def incr(self, _key):
            raise RedisError("Redis package is not installed")

        def expire(self, _key, _seconds):
            raise RedisError("Redis package is not installed")


redis_client = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)


def cache_get_json(key: str) -> Any | None:
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except (RedisError, json.JSONDecodeError):
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 60) -> None:
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except RedisError:
        # PostgreSQL remains authoritative if Redis is unavailable.
        return
