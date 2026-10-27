"""Tests for bookmaker accessibility / reliability filtering."""

from analyzer.filters import is_unreliable, matches_any, prepare_events
from factories import make_book, make_event, make_outcome


def book(title, key=None):
    b = make_book(title, "h2h", [make_outcome("Home", 100), make_outcome("Away", 100)])
    if key:
        b["key"] = key
    return b


def titles(events):
    return [b["title"] for e in events for b in e["bookmakers"]]


def test_patterns_ignore_spacing_and_case():
    assert matches_any(book("Marathon Bet"), {"marathonbet"})
    assert matches_any(book("ESPN BET"), {"espn bet"})
    assert matches_any(book("888sport"), {"888"})
    assert not matches_any(book("DraftKings"), {"fanduel"})


def test_pattern_can_match_the_key():
    assert matches_any(book("Some Brand", key="onexbet_1xbet"), {"1xbet"})


def test_unreliable_books_are_detected():
    assert is_unreliable(book("1xBet"))
    assert is_unreliable(book("Unibet (NL)"))
    assert not is_unreliable(book("Pinnacle"))


def test_prepare_events_applies_all_filters():
    event = make_event([book("Pinnacle"), book("1xBet"), book("DraftKings"), book("Marathon Bet")])

    assert titles(prepare_events([event])) == ["Pinnacle", "DraftKings", "Marathon Bet"]
    assert titles(prepare_events([event], bet_from="brazil")) == ["Pinnacle", "Marathon Bet"]
    assert titles(prepare_events([event], bet_from="usa")) == ["DraftKings"]
    assert "1xBet" in titles(prepare_events([event], include_unreliable=True))
    assert titles(prepare_events([event], excluded_titles=frozenset({"Pinnacle"}))) == [
        "DraftKings", "Marathon Bet",
    ]


def test_prepare_events_does_not_mutate_input():
    event = make_event([book("1xBet")])
    prepare_events([event])
    assert titles([event]) == ["1xBet"]


def test_games_in_progress_are_dropped_by_default():
    upcoming = make_event([book("Pinnacle")])
    started = make_event([book("Pinnacle")])
    started["commence_time"] = "2020-01-01T00:00:00Z"

    assert prepare_events([upcoming, started]) == [upcoming]
    assert len(prepare_events([upcoming, started], include_started=True)) == 2
