from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class RateLimitExceeded(Exception):
    pass


class AuthRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(
        self,
        bucket: str,
        identity: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        key = f"{bucket}:{identity.lower()}"
        now = monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= window_seconds:
                events.popleft()
            if len(events) >= limit:
                raise RateLimitExceeded
            events.append(now)

    def reset(self, bucket: str, identity: str) -> None:
        key = f"{bucket}:{identity.lower()}"
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


auth_rate_limiter = AuthRateLimiter()
