from datetime import UTC, datetime

from app.core.cache import RedisError, redis_client


def allow_request(identity: str, path: str) -> tuple[bool, int]:
    """Redis-backed fixed-window rate limit.

    Redis is intentionally non-authoritative. If it is unavailable, the request is
    allowed and the platform continues using PostgreSQL as its source of truth.
    """
    if path.endswith("/auth/login"):
        limit = 20
    elif "/payments/" in path or "/open-banking/" in path:
        limit = 60
    else:
        limit = 180

    window = datetime.now(UTC).strftime("%Y%m%d%H%M")
    key = f"rate:{identity}:{path}:{window}"
    try:
        count = int(redis_client.incr(key))
        if count == 1:
            redis_client.expire(key, 70)
        return count <= limit, limit
    except (RedisError, AttributeError, TypeError, ValueError):
        return True, limit
