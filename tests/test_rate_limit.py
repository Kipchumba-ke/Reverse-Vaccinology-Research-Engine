import pytest
from flask import Flask

from app.services.rate_limit import (
    EndpointRule,
    MemoryStorage,
    RateLimit,
    RateLimiter,
    RedisStorage,
    build_default_rules,
    build_rate_limiter_from_environment,
    install_rate_limiting,
)


class FakeClock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


def make_app(limiter, rules, get_user_id=None):
    app = Flask(__name__)

    @app.post("/api/login")
    def login():
        return {"ok": True}

    @app.post("/api/analyses")
    def analyses():
        return {"ok": True}

    @app.get("/api/status")
    def status():
        return {"ok": True}

    install_rate_limiting(app, limiter, rules, get_user_id=get_user_id)
    return app


def test_parse_rate_limit():
    assert RateLimit.parse("10/minute") == RateLimit(10, 60)
    assert RateLimit.parse(" 3/Hour ") == RateLimit(3, 3600)
    assert RateLimit.parse("1/second") == RateLimit(1, 1)


@pytest.mark.parametrize("text", ["", "10", "x/minute", "10/week", "0/minute", "-1/hour"])
def test_invalid_rate_limit_is_rejected(text):
    with pytest.raises(ValueError):
        RateLimit.parse(text)


def test_requests_over_the_limit_are_rejected_with_retry_after():
    clock = FakeClock()
    limiter = RateLimiter(MemoryStorage(clock=clock))
    rules = [
        EndpointRule(
            bucket="auth",
            limit=RateLimit(2, 60),
            methods=frozenset({"POST"}),
            paths=frozenset({"/api/login"}),
        )
    ]
    client = make_app(limiter, rules).test_client()

    assert client.post("/api/login").status_code == 200
    assert client.post("/api/login").status_code == 200

    blocked = client.post("/api/login")

    assert blocked.status_code == 429
    assert blocked.get_json() == {
        "error": "Too many requests. Please try again later."
    }
    assert int(blocked.headers["Retry-After"]) >= 1


def test_limit_resets_in_the_next_window():
    clock = FakeClock()
    limiter = RateLimiter(MemoryStorage(clock=clock))
    rules = [EndpointRule(bucket="auth", limit=RateLimit(1, 60))]
    client = make_app(limiter, rules).test_client()

    assert client.get("/api/status").status_code == 200
    assert client.get("/api/status").status_code == 429

    clock.now += 61

    assert client.get("/api/status").status_code == 200


def test_rules_only_apply_to_matching_paths_and_methods():
    limiter = RateLimiter(MemoryStorage(clock=FakeClock()))
    rules = [
        EndpointRule(
            bucket="auth",
            limit=RateLimit(1, 60),
            methods=frozenset({"POST"}),
            paths=frozenset({"/api/login"}),
        )
    ]
    client = make_app(limiter, rules).test_client()

    for _ in range(5):
        assert client.get("/api/status").status_code == 200

    assert client.post("/api/login").status_code == 200
    assert client.post("/api/login").status_code == 429


def test_user_rules_count_each_user_separately():
    limiter = RateLimiter(MemoryStorage(clock=FakeClock()))
    rules = [
        EndpointRule(
            bucket="analysis",
            limit=RateLimit(1, 3600),
            per="user",
            methods=frozenset({"POST"}),
            paths=frozenset({"/api/analyses"}),
        )
    ]

    def get_user_id(req):
        return req.headers["X-Test-User"]

    client = make_app(limiter, rules, get_user_id=get_user_id).test_client()

    assert client.post("/api/analyses", headers={"X-Test-User": "a"}).status_code == 200
    assert client.post("/api/analyses", headers={"X-Test-User": "a"}).status_code == 429
    assert client.post("/api/analyses", headers={"X-Test-User": "b"}).status_code == 200


def test_user_rule_falls_back_to_ip_without_a_valid_user():
    limiter = RateLimiter(MemoryStorage(clock=FakeClock()))
    rules = [
        EndpointRule(
            bucket="analysis",
            limit=RateLimit(1, 3600),
            per="user",
            paths=frozenset({"/api/analyses"}),
        )
    ]

    def get_user_id(req):
        raise ValueError("Authentication required.")

    client = make_app(limiter, rules, get_user_id=get_user_id).test_client()

    assert client.post("/api/analyses").status_code == 200
    assert client.post("/api/analyses").status_code == 429


def test_options_requests_are_never_limited():
    limiter = RateLimiter(MemoryStorage(clock=FakeClock()))
    rules = [EndpointRule(bucket="all", limit=RateLimit(1, 60))]
    client = make_app(limiter, rules).test_client()

    for _ in range(5):
        assert client.options("/api/status").status_code != 429


def test_storage_failure_fails_open():
    class BrokenStorage:
        def hit(self, key, window_seconds):
            raise ConnectionError("store down")

    limiter = RateLimiter(BrokenStorage())
    rules = [EndpointRule(bucket="all", limit=RateLimit(1, 60))]
    client = make_app(limiter, rules).test_client()

    for _ in range(3):
        assert client.get("/api/status").status_code == 200


def test_redis_storage_counts_and_sets_expiry():
    class FakePipeline:
        def __init__(self, store):
            self.store = store
            self.ops = []

        def incr(self, key):
            self.ops.append(("incr", key))

        def expire(self, key, seconds):
            self.ops.append(("expire", key, seconds))

        def execute(self):
            results = []
            for op in self.ops:
                if op[0] == "incr":
                    self.store[op[1]] = self.store.get(op[1], 0) + 1
                    results.append(self.store[op[1]])
                else:
                    self.store.setdefault("expiries", {})[op[1]] = op[2]
                    results.append(True)
            return results

    class FakeRedis:
        def __init__(self):
            self.store = {}

        def pipeline(self):
            return FakePipeline(self.store)

    client = FakeRedis()
    storage = RedisStorage(client, clock=FakeClock(1_000_000.0))

    first, seconds_left = storage.hit("auth:1.2.3.4", 60)
    second, _ = storage.hit("auth:1.2.3.4", 60)

    assert (first, second) == (1, 2)
    assert 1 <= seconds_left <= 60
    assert list(client.store["expiries"].values())[0] == seconds_left + 1


def test_defaults_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_AUTH", "3/minute")
    monkeypatch.setenv("RATE_LIMIT_ANALYSIS", "5/day")
    monkeypatch.delenv("RATE_LIMIT_DEFAULT", raising=False)

    rules = {rule.bucket: rule for rule in build_default_rules()}

    assert rules["auth"].limit == RateLimit(3, 60)
    assert rules["analysis"].limit == RateLimit(5, 86400)
    assert rules["default"].limit == RateLimit(300, 60)
    assert rules["analysis"].per == "user"
    assert "/api/login" in rules["auth"].paths


def test_limiter_can_be_disabled(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "0")

    assert build_rate_limiter_from_environment() is None


def test_limiter_uses_memory_storage_without_a_redis_url(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "1")
    monkeypatch.delenv("RATE_LIMIT_STORAGE_URL", raising=False)

    assert isinstance(build_rate_limiter_from_environment(), RateLimiter)
