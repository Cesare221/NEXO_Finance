from collections import defaultdict, deque
import hashlib
from threading import Lock
from time import monotonic

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


class RateLimitUnavailable(Exception):
    pass


class AuthRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._redis = Redis.from_url(settings.redis_url) if settings.redis_url else None

    @staticmethod
    def _key(bucket: str, identity: str) -> str:
        identity_hash = hashlib.sha256(identity.casefold().encode("utf-8")).hexdigest()
        return f"nexo:rate-limit:{bucket}:{identity_hash}"

    def check(
        self,
        bucket: str,
        identity: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        key = self._key(bucket, identity)
        if self._redis is not None:
            try:
                current = self._redis.eval(
                    """
                    local current = redis.call('INCR', KEYS[1])
                    if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
                    return current
                    """,
                    1,
                    key,
                    window_seconds,
                )
                if int(current) > limit:
                    ttl = self._redis.ttl(key)
                    raise RateLimitExceeded(max(int(ttl), 1))
                return
            except RateLimitExceeded:
                raise
            except RedisError as error:
                raise RateLimitUnavailable from error

        now = monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= window_seconds:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])))
                raise RateLimitExceeded(retry_after)
            events.append(now)

    def reset(self, bucket: str, identity: str) -> None:
        key = self._key(bucket, identity)
        if self._redis is not None:
            try:
                self._redis.delete(key)
                return
            except RedisError as error:
                raise RateLimitUnavailable from error
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        if self._redis is not None:
            return
        with self._lock:
            self._events.clear()


auth_rate_limiter = AuthRateLimiter()
