# =============================================================================
# export.py
# Convert event analyses (see arbitrage.analyze_event) into pandas DataFrames
# and CSV files.
#
#   detailed → one row per outcome (which side, which book, what price, stake)
#   summary  → one row per event (efficiency, arbitrage flag, best single price)
# =============================================================================

from pathlib import Path

import pandas as pd


def _round_or_none(value: float | None, digits: int) -> float | None:
    return round(value, digits) if value is not None else None


def analyses_to_dataframe(analyses: list) -> pd.DataFrame:
    """Return one row per outcome across all analysed events."""
    rows = []

    for analysis in analyses:
        for row in analysis["results"]:
            rows.append({
                "event":            analysis["event"],
                "sport":            analysis["sport"],
                "commence_time":    analysis["commence_time"],
                "implied_prob_sum": round(analysis["implied_prob_sum"], 4),
                "arbitrage":        analysis["arbitrage"],
                "profit":           _round_or_none(analysis["profit"], 2),
                "roi":              _round_or_none(analysis["roi"], 2),
                "outcome":          row["outcome"],
                "point":            row.get("point"),
                "bookmaker":        row["bookmaker"],
                "american_odds":    row["american_odds"],
                "decimal_odds":     round(row["decimal_odds"], 4),
                "stake":            _round_or_none(row.get("stake"), 2),
            })

    return pd.DataFrame(rows)


def analyses_to_summary_dataframe(analyses: list) -> pd.DataFrame:
    """Return one row per event, including its single highest-priced outcome."""
    rows = []

    for analysis in analyses:
        results = analysis.get("results", [])
        best = max(results, key=lambda r: r.get("decimal_odds", 0), default={})

        rows.append({
            "event":              analysis["event"],
            "sport":              analysis["sport"],
            "commence_time":      analysis["commence_time"],
            "line":               analysis.get("line"),
            "implied_prob_sum":   round(analysis["implied_prob_sum"], 4),
            "arbitrage":          analysis["arbitrage"],
            "profit":             _round_or_none(analysis["profit"], 2),
            "roi":                _round_or_none(analysis["roi"], 2),
            "best_outcome":       best.get("outcome"),
            "best_bookmaker":     best.get("bookmaker"),
            "best_american_odds": best.get("american_odds"),
            "best_decimal_odds":  _round_or_none(best.get("decimal_odds"), 4),
        })

    return pd.DataFrame(rows)


def export_detailed_csv(path: str | Path, analyses: list) -> pd.DataFrame:
    """Write the per-outcome table to `path` and return it."""
    df = analyses_to_dataframe(analyses)
    df.to_csv(path, index=False)
    return df


def export_summary_csv(path: str | Path, analyses: list) -> pd.DataFrame:
    """Write the per-event table to `path` and return it."""
    df = analyses_to_summary_dataframe(analyses)
    df.to_csv(path, index=False)
    return df
