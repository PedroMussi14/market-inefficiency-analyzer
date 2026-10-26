"""Tests for +EV detection against Pinnacle's de-vigged line."""

import pytest

from analyzer.ev import fair_probabilities, find_ev_bets
from factories import make_book, make_event, make_outcome


def test_fair_probabilities_remove_the_vig():
    event = make_event([
        make_book("Pinnacle", "h2h", [make_outcome("Home", -110), make_outcome("Away", -110)]),
    ])
    probs = fair_probabilities(event)

    assert probs == {"Home": pytest.approx(0.5), "Away": pytest.approx(0.5)}


def test_finds_price_better_than_fair_odds():
    event = make_event([
        make_book("Pinnacle", "h2h", [make_outcome("Home", -110), make_outcome("Away", -110)]),
        make_book("Book A", "h2h", [make_outcome("Home", 110), make_outcome("Away", -130)]),
    ])
    (bet,) = find_ev_bets(event)

    # Fair probability 50% at decimal 2.10 → EV = 2.10 * 0.5 - 1 = +5%
    assert bet["bookmaker"] == "Book A"
    assert bet["outcome"] == "Home"
    assert bet["true_prob"] == pytest.approx(50.0)
    assert bet["ev_pct"] == pytest.approx(5.0)


def test_bets_are_sorted_by_edge():
    event = make_event([
        make_book("Pinnacle", "h2h", [make_outcome("Home", -110), make_outcome("Away", -110)]),
        make_book("Book A", "h2h", [make_outcome("Home", 105), make_outcome("Away", -130)]),
        make_book("Book B", "h2h", [make_outcome("Home", 120), make_outcome("Away", -150)]),
    ])
    bets = find_ev_bets(event)

    assert [b["bookmaker"] for b in bets] == ["Book B", "Book A"]


def test_no_sharp_book_means_no_ev_bets():
    event = make_event([
        make_book("Book A", "h2h", [make_outcome("Home", 300), make_outcome("Away", 300)]),
    ])
    assert find_ev_bets(event) == []


def test_spread_prices_are_only_compared_on_the_same_line():
    """Pinnacle -3.5 must not be used to judge another book's -6.5 price."""
    event = make_event([
        make_book("Pinnacle", "spreads", [
            make_outcome("Home", -110, -3.5), make_outcome("Away", -110, 3.5),
        ]),
        make_book("Book A", "spreads", [
            make_outcome("Home", 150, -6.5), make_outcome("Away", -190, 6.5),
        ]),
    ])
    assert find_ev_bets(event, selected_market="spreads") == []
