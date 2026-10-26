"""Tests for the arbitrage maths and event analysis."""

import pytest

from analyzer.arbitrage import (
    analyze_event,
    build_deep_link,
    calculate_profit,
    calculate_roi,
    calculate_stakes,
)
from factories import make_book, make_event, make_outcome

# =============================================================================
# Stake sizing, profit and ROI
# =============================================================================

def test_stakes_equalise_payout_across_outcomes():
    odds = [2.5, 1.9, 4.0]
    stakes = calculate_stakes(100, odds)

    assert sum(stakes) == pytest.approx(100)
    payouts = [s * o for s, o in zip(stakes, odds, strict=True)]
    assert max(payouts) - min(payouts) == pytest.approx(0, abs=1e-9)


def test_profit_is_worst_case_payout_minus_bankroll():
    odds = [2.1, 2.1]
    assert calculate_profit(100, calculate_stakes(100, odds), odds) == pytest.approx(5.0)


def test_roi_is_profit_as_percentage_of_bankroll():
    assert calculate_roi(250, 5) == pytest.approx(2.0)


# =============================================================================
# Moneyline (h2h) analysis
# =============================================================================

def test_detects_two_way_arbitrage(two_way_arb_event):
    analysis = analyze_event(two_way_arb_event, bankroll=100)

    assert analysis["arbitrage"] is True
    assert analysis["implied_prob_sum"] == pytest.approx(0.952381, rel=1e-6)
    assert analysis["profit"] == pytest.approx(5.0)
    assert analysis["roi"] == pytest.approx(5.0)
    assert {r["bookmaker"] for r in analysis["results"]} == {"Book A", "Book B"}
    assert sum(r["stake"] for r in analysis["results"]) == pytest.approx(100)


def test_efficient_market_is_not_arbitrage():
    event = make_event([
        make_book("Book A", "h2h", [make_outcome("Home", -110), make_outcome("Away", -110)]),
    ])
    analysis = analyze_event(event)

    assert analysis["arbitrage"] is False
    assert analysis["implied_prob_sum"] > 1
    assert analysis["profit"] is None and analysis["roi"] is None


def test_event_with_single_outcome_is_skipped():
    event = make_event([make_book("Book A", "h2h", [make_outcome("Home", 200)])])
    assert analyze_event(event) is None


# =============================================================================
# Bug 2: missing outcomes must never produce a "guaranteed" profit
# =============================================================================

def test_soccer_match_without_draw_price_is_skipped():
    """Without a Draw price, Home+Away alone looks like a 4.8% arb but isn't one."""
    event = make_event(
        [
            make_book("Book A", "h2h", [make_outcome("Home", 110), make_outcome("Away", -150)]),
            make_book("Book B", "h2h", [make_outcome("Home", -150), make_outcome("Away", 110)]),
        ],
        sport_key="soccer_epl",
    )
    assert analyze_event(event) is None


def test_outcome_missing_from_union_is_skipped():
    """If one book prices a 3-way market, every arb must cover all 3 outcomes."""
    event = make_event([
        make_book("Book A", "h2h", [
            make_outcome("Home", 150), make_outcome("Draw", 220), make_outcome("Away", 180),
        ]),
        make_book("Book B", "h2h", [make_outcome("Home", 300), make_outcome("Away", 300)]),
    ])
    analysis = analyze_event(event)

    assert analysis is not None
    assert {r["outcome"] for r in analysis["results"]} == {"Home", "Draw", "Away"}


def test_three_way_soccer_arbitrage_uses_all_outcomes():
    event = make_event(
        [
            make_book("Book A", "h2h", [
                make_outcome("Home", 200), make_outcome("Draw", 200), make_outcome("Away", 150),
            ]),
            make_book("Book B", "h2h", [
                make_outcome("Home", 150), make_outcome("Draw", 250), make_outcome("Away", 250),
            ]),
        ],
        sport_key="soccer_epl",
    )
    analysis = analyze_event(event)

    # Best prices 3.0 / 3.5 / 3.5 -> implied sum 0.9048
    assert analysis["arbitrage"] is True
    assert len(analysis["results"]) == 3
    assert analysis["implied_prob_sum"] == pytest.approx(1 / 3 + 2 / 3.5)


# =============================================================================
# Bug 1: spreads/totals must be evaluated one line at a time
# =============================================================================

def test_spread_arbitrage_on_one_line_is_found_despite_other_lines():
    event = make_event(
        [
            make_book("Book A", "spreads", [
                make_outcome("Home", 110, -3.5), make_outcome("Away", -150, 3.5),
            ]),
            make_book("Book B", "spreads", [
                make_outcome("Home", -150, -3.5), make_outcome("Away", 110, 3.5),
            ]),
            make_book("Book C", "spreads", [
                make_outcome("Home", 100, -4.5), make_outcome("Away", -120, 4.5),
            ]),
        ],
    )
    analysis = analyze_event(event, selected_market="spreads")

    assert analysis["arbitrage"] is True
    assert analysis["implied_prob_sum"] == pytest.approx(2 / 2.1)
    assert analysis["line"] == -3.5
    assert {(r["outcome"], r["point"]) for r in analysis["results"]} == {
        ("Home", -3.5), ("Away", 3.5),
    }


def test_spread_lines_are_never_mixed():
    """Home -3.5 @ 3.0 and Away +6.5 @ 3.0 sum to 0.667, but they are different bets."""
    event = make_event([
        make_book("Book A", "spreads", [
            make_outcome("Home", 200, -3.5), make_outcome("Away", -400, 3.5),
        ]),
        make_book("Book B", "spreads", [
            make_outcome("Home", -400, -6.5), make_outcome("Away", 200, 6.5),
        ]),
    ])
    analysis = analyze_event(event, selected_market="spreads")

    assert analysis["arbitrage"] is False
    assert len(analysis["results"]) == 2
    points = {r["outcome"]: r["point"] for r in analysis["results"]}
    assert points["Home"] == -points["Away"]


def test_totals_pick_the_line_closest_to_arbitrage():
    event = make_event([
        make_book("Book A", "totals", [
            make_outcome("Over", 110, 220.5), make_outcome("Under", -150, 220.5),
        ]),
        make_book("Book B", "totals", [
            make_outcome("Over", -150, 220.5), make_outcome("Under", 110, 220.5),
        ]),
        make_book("Book C", "totals", [
            make_outcome("Over", -110, 221.5), make_outcome("Under", -110, 221.5),
        ]),
    ])
    analysis = analyze_event(event, selected_market="totals")

    assert analysis["arbitrage"] is True
    assert analysis["line"] == 220.5
    assert {r["point"] for r in analysis["results"]} == {220.5}


def test_line_market_without_a_complete_pair_is_skipped():
    event = make_event([
        make_book("Book A", "totals", [make_outcome("Over", 110, 220.5)]),
        make_book("Book B", "totals", [make_outcome("Under", 110, 221.5)]),
    ])
    assert analyze_event(event, selected_market="totals") is None


# =============================================================================
# Deep links
# =============================================================================

def test_deep_link_prefers_outcome_level_link():
    link = build_deep_link(
        "Book A",
        {"link": "https://book.example/bet/1"},
        {"link": "https://book.example/event"},
        {"link": "https://book.example"},
    )
    assert link == "https://book.example/bet/1"


def test_homepage_link_is_replaced_by_sid_template():
    link = build_deep_link("BetUS", {}, {}, {"link": "https://www.betus.com.pa/", "sid": "123"})
    assert link == "https://www.betus.com.pa/sportsbook/#/event/main/123"


def test_deep_link_is_none_when_nothing_usable():
    assert build_deep_link("Unknown Book", {}, {}, {}) is None
