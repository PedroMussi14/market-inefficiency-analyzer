"""The Odds API provider: failures are reported without leaking the API key."""

import pytest
import requests

from analyzer.providers.odds_api import OddsApiError, OddsApiProvider

SECRET = "sk_test_do_not_leak"


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.ok = status < 400

    def json(self):
        return self._body


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("API_KEY", SECRET)
    return OddsApiProvider()


def test_spent_quota_is_explained_without_the_key(provider, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(
        401, {"message": "Usage quota has been reached."}, {"x-requests-remaining": "0", "x-requests-used": "500"},
    ))
    with pytest.raises(OddsApiError) as err:
        provider.get_odds("basketball_nba")

    assert err.value.quota_exhausted
    assert "quota" in str(err.value)
    assert SECRET not in str(err.value)
    assert provider.get_quota_info() == {"remaining": "0", "used": "500"}


def test_connection_errors_do_not_echo_the_url(provider, monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError(f"Max retries exceeded with url: /v4/sports?apiKey={SECRET}")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(OddsApiError) as err:
        provider.get_sports()

    assert SECRET not in str(err.value)
    assert err.value.__cause__ is None and err.value.__suppress_context__
