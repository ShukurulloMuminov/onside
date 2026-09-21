import pytest
from django.core.cache import cache

pytestmark = pytest.mark.django_db

# DRF's SimpleRateThrottle binds THROTTLE_RATES as a class attribute at
# first import of rest_framework.throttling, reading settings.REST_FRAMEWORK
# at that moment — later mutating settings via the `settings` fixture does
# NOT re-bind it (there's no signal-driven refresh for this specific
# attribute, unlike api_settings itself). So these tests exercise the real
# configured rate (see config/settings.py DEFAULT_THROTTLE_RATES["auth"])
# rather than trying to override it per-test.
AUTH_RATE_PER_MINUTE = 10


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    # DRF's throttle counters live in Django's cache, keyed by scope + IP —
    # clear before/after so tests don't bleed into each other or into the
    # rest of the suite (all requests come from the same test-client IP).
    cache.clear()
    yield
    cache.clear()


def test_login_is_throttled_after_repeated_attempts(api_client):
    payload = {"username": "nobody", "password": "wrong"}
    statuses = [
        api_client.post("/api/v1/auth/login/", payload, format="json").status_code
        for _ in range(AUTH_RATE_PER_MINUTE + 1)
    ]

    # Every attempt up to the configured rate is rejected as bad
    # credentials (401); the one that exceeds it is throttled (429).
    assert statuses[:AUTH_RATE_PER_MINUTE] == [401] * AUTH_RATE_PER_MINUTE
    assert statuses[AUTH_RATE_PER_MINUTE] == 429


def test_register_is_throttled_after_repeated_attempts(api_client):
    def attempt(n):
        return api_client.post(
            "/api/v1/auth/register/",
            {"username": f"throttle_user_{n}", "password": "not-a-real-password"},
            format="json",
        ).status_code

    statuses = [attempt(i) for i in range(AUTH_RATE_PER_MINUTE + 1)]

    assert 429 not in statuses[:AUTH_RATE_PER_MINUTE]
    assert statuses[AUTH_RATE_PER_MINUTE] == 429


def test_unrelated_endpoints_are_not_subject_to_the_tight_auth_scope(api_client):
    # A public, unauthenticated, non-auth endpoint should only hit the much
    # more generous "anon" scope, not "auth" — confirms the tight limit is
    # scoped to login/register/Google, not applied globally.
    statuses = [
        api_client.get("/api/v1/tournaments/").status_code for _ in range(AUTH_RATE_PER_MINUTE + 1)
    ]
    assert all(status == 200 for status in statuses)
