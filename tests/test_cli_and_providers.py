"""Tests for the provider registry and the command-line scanner."""

import pytest

from analyzer import cli, providers
from analyzer.providers.base import Provider


def test_registry_contains_expected_providers():
    assert {"odds_api", "brodds_local", "opticodds"} <= set(providers.PROVIDERS)
    assert all(isinstance(p, Provider) for p in providers.list_providers())


def test_unknown_provider_raises():
    with pytest.raises(KeyError):
        providers.get_provider("does_not_exist")


def test_odds_api_requires_a_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    assert not providers.get_provider("odds_api").is_configured()

    monkeypatch.setenv("API_KEY", "test-key")
    assert providers.get_provider("odds_api").is_configured()


def test_planned_provider_is_not_implemented():
    with pytest.raises(NotImplementedError):
        providers.get_provider("opticodds").get_sports()


class FakeProvider(Provider):
    name = "fake"

    def __init__(self, events):
        self.events = events

    def get_sports(self):
        return []

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True):
        return self.events


def test_cli_reports_arbitrage_and_writes_csvs(monkeypatch, tmp_path, capsys, two_way_arb_event):
    monkeypatch.setattr(cli, "get_provider", lambda name: FakeProvider([two_way_arb_event]))

    exit_code = cli.main(["--output-dir", str(tmp_path)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PROFITABLE ARBITRAGE OPPORTUNITIES" in out
    assert "Guaranteed Profit: $5.00" in out
    assert (tmp_path / "detailed.csv").exists()
    assert (tmp_path / "summary.csv").exists()


def test_cli_fails_cleanly_without_configuration(monkeypatch, capsys):
    monkeypatch.delenv("API_KEY", raising=False)

    assert cli.main(["--provider", "odds_api"]) == 1
    assert "not configured" in capsys.readouterr().err
