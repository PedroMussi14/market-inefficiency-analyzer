"""Tests for DataFrame and CSV export of analyses."""

import pandas as pd
import pytest

from analyzer.arbitrage import analyze_event
from analyzer.export import (
    analyses_to_dataframe,
    analyses_to_summary_dataframe,
    export_detailed_csv,
    export_summary_csv,
)


@pytest.fixture
def analyses(two_way_arb_event):
    return [analyze_event(two_way_arb_event, bankroll=100)]


def test_detailed_has_one_row_per_outcome(analyses):
    df = analyses_to_dataframe(analyses)

    assert len(df) == 2
    assert set(df["bookmaker"]) == {"Book A", "Book B"}
    assert df["stake"].sum() == pytest.approx(100)
    assert df["implied_prob_sum"].iloc[0] == 0.9524


def test_summary_has_one_row_per_event(analyses):
    df = analyses_to_summary_dataframe(analyses)

    assert len(df) == 1
    row = df.iloc[0]
    assert bool(row["arbitrage"]) is True
    assert row["profit"] == pytest.approx(5.0)
    assert row["best_decimal_odds"] == pytest.approx(2.1)


def test_empty_input_gives_empty_frames():
    assert analyses_to_dataframe([]).empty
    assert analyses_to_summary_dataframe([]).empty


def test_csv_files_round_trip(analyses, tmp_path):
    export_detailed_csv(tmp_path / "detailed.csv", analyses)
    export_summary_csv(tmp_path / "summary.csv", analyses)

    assert len(pd.read_csv(tmp_path / "detailed.csv")) == 2
    assert len(pd.read_csv(tmp_path / "summary.csv")) == 1
