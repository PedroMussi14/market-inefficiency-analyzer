"""Tests for odds-format conversion and implied probability."""

import pytest

from analyzer.odds import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    implied_probability_sum,
)


@pytest.mark.parametrize(
    ("american", "decimal"),
    [(150, 2.5), (100, 2.0), (-200, 1.5), (-110, 1 + 100 / 110)],
)
def test_american_to_decimal(american, decimal):
    assert american_to_decimal(american) == pytest.approx(decimal)


@pytest.mark.parametrize(
    ("decimal", "american"),
    [(2.5, 150), (2.0, 100), (1.5, -200), (1.91, -110)],
)
def test_decimal_to_american(decimal, american):
    assert decimal_to_american(decimal) == american


@pytest.mark.parametrize("american", [-500, -110, 100, 125, 900])
def test_round_trip_is_stable(american):
    assert decimal_to_american(american_to_decimal(american)) == american


@pytest.mark.parametrize("bad", [1.0, 0.5, 0])
def test_decimal_to_american_rejects_impossible_prices(bad):
    with pytest.raises(ValueError):
        decimal_to_american(bad)


def test_implied_probability():
    assert implied_probability(4.0) == pytest.approx(0.25)


def test_implied_probability_sum():
    assert implied_probability_sum([2.0, 2.0]) == pytest.approx(1.0)
    assert implied_probability_sum([2.1, 2.1]) == pytest.approx(0.952381, rel=1e-6)
    assert implied_probability_sum(x for x in [3.0, 3.0, 3.0]) == pytest.approx(1.0)
