"""Fixed-window rate limiting for the HTTP API.

Counters live in memory by default, which is enough for a single process.
Set RATE_LIMIT_STORAGE_URL to a Redis URL so every gunicorn worker shares
the same counters. If the counter store fails, requests are allowed rather
than blocked, and a warning is logged.

Environment variables:
    RATE_LIMIT_ENABLED       "1" (default) or "0" to switch limiting off
    RATE_LIMIT_STORAGE_URL   Redis URL; in-memory counters when unset
    RATE_LIMIT_AUTH          login and registration, per IP (default 10/minute)
    RATE_LIMIT_ANALYSIS      analysis submission, per user (default 30/hour)
    RATE_LIMIT_DEFAULT       every request, per IP (default 300/minute)
    TRUSTED_PROXY_COUNT      number of reverse proxies in front of the app
"""

import logging
import os
import threading
import time
from dataclasses import dataclass

from flask import jsonify, request


LOGGER = logging.getLogger(__name__)

_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


@dataclass(frozen=True)
class RateLimit:
    count: int
    window_seconds: int

    @classmethod
    def parse(cls, text: str) -> "RateLimit":
        """Parse text such as '10/minute' into a RateLimit."""
        try:
            count_text, unit = text.strip().lower().split("/")
            count = int(count_text)
            window_seconds = _UNIT_SECONDS[unit.strip()]
        except (ValueError, KeyError, AttributeError) as error:
            raise ValueError(
                f"Invalid rate limit '{text}'. Use the form "
                "'<count>/<second|minute|hour|day>'."
            ) from error

        if count <= 0:
            raise ValueError("Rate limit count must be greater than zero.")

        return cls(count=count, window_seconds=window_seconds)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after: int


@dataclass(frozen=True)
class EndpointRule:
    """A limit applied to matching requests.

    paths=None matches every path. per is "ip" or "user".
    """

    bucket: str
    limit: RateLimit
    per: str = "ip"
    methods: frozenset = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
    paths: frozenset | None = None

    def matches(self, method: str, path: str) -> bool:
        if method not in self.methods:
            return False

        return self.paths is None or path in self.paths


class MemoryStorage:
    """Thread-safe in-process counters."""

    def __init__(self, clock=time.time):
        self._clock = clock
        self._counts = {}
        self._lock = threading.Lock()

    def hit(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Count one request; return (count in window, seconds left)."""
        now = self._clock()
        window_id = int(now // window_seconds)
        seconds_left = max(1, int(window_seconds - (now % window_seconds)))

        with self._lock:
            self._counts = {
                stored_key: stored
                for stored_key, stored in self._counts.items()
                if stored[1] >= now
            }

            counter_key = f"{key}:{window_id}"
            count, _expires = self._counts.get(counter_key, (0, 0))
            count += 1
            self._counts[counter_key] = (count, now + seconds_left)

        return count, seconds_left


class RedisStorage:
    """Counters shared between processes through Redis."""

    def __init__(self, client, prefix: str = "ratelimit", clock=time.time):
        self._client = client
        self._prefix = prefix
        self._clock = clock

    def hit(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = self._clock()
        window_id = int(now // window_seconds)
        seconds_left = max(1, int(window_seconds - (now % window_seconds)))
        counter_key = f"{self._prefix}:{key}:{window_id}"

        pipeline = self._client.pipeline()
        pipeline.incr(counter_key)
        pipeline.expire(counter_key, seconds_left + 1)
        count, _ = pipeline.execute()

        return int(count), seconds_left


class RateLimiter:
    def __init__(self, storage, logger=LOGGER):
        self._storage = storage
        self._logger = logger

    def check(self, bucket: str, identity: str, limit: RateLimit):
        key = f"{bucket}:{identity}"

        try:
            count, seconds_left = self._storage.hit(
                key,
                limit.window_seconds,
            )
        except Exception:  # Fail open: never block users on a store outage.
            self._logger.warning(
                "Rate-limit storage failed; allowing request.",
                exc_info=True,
            )
            return RateLimitResult(allowed=True, retry_after=0)

        if count > limit.count:
            return RateLimitResult(allowed=False, retry_after=seconds_left)

        return RateLimitResult(allowed=True, retry_after=0)


def build_default_rules() -> list[EndpointRule]:
    """Build the API rules, reading limits from the environment."""
    return [
        EndpointRule(
            bucket="default",
            limit=RateLimit.parse(
                os.environ.get("RATE_LIMIT_DEFAULT", "300/minute")
            ),
            per="ip",
        ),
        EndpointRule(
            bucket="auth",
            limit=RateLimit.parse(
                os.environ.get("RATE_LIMIT_AUTH", "10/minute")
            ),
            per="ip",
            methods=frozenset({"POST"}),
            paths=frozenset({"/api/login", "/api/register"}),
        ),
        EndpointRule(
            bucket="analysis",
            limit=RateLimit.parse(
                os.environ.get("RATE_LIMIT_ANALYSIS", "30/hour")
            ),
            per="user",
            methods=frozenset({"POST"}),
            paths=frozenset({
                "/api/analyses",
                "/api/analyze",
                "/api/v1/analyze",
            }),
        ),
    ]


def build_rate_limiter_from_environment() -> RateLimiter | None:
    """Return a limiter, or None when RATE_LIMIT_ENABLED is "0"."""
    if os.environ.get("RATE_LIMIT_ENABLED", "1").strip() == "0":
        return None

    storage_url = os.environ.get("RATE_LIMIT_STORAGE_URL")

    if storage_url:
        import redis

        return RateLimiter(RedisStorage(redis.Redis.from_url(storage_url)))

    return RateLimiter(MemoryStorage())


def _client_address() -> str:
    return request.remote_addr or "unknown"


def install_rate_limiting(app, limiter, rules, get_user_id=None):
    """Reject requests that exceed any matching rule with HTTP 429.

    get_user_id(request) should return the authenticated user's id or raise
    ValueError. Requests without a valid user are limited by IP address.
    """

    @app.before_request
    def enforce_rate_limits():
        if request.method == "OPTIONS":
            return None

        for rule in rules:
            if not rule.matches(request.method, request.path):
                continue

            identity = _client_address()

            if rule.per == "user" and get_user_id is not None:
                try:
                    identity = f"user-{get_user_id(request)}"
                except ValueError:
                    pass

            result = limiter.check(rule.bucket, identity, rule.limit)

            if not result.allowed:
                response = jsonify({
                    "error": "Too many requests. Please try again later.",
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(result.retry_after)
                return response

        return None
