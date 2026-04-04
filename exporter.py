import pandas as pd


def analyses_to_dataframe(analyses):
    rows = []

    for analysis in analyses:
        for row in analysis["results"]:
            rows.append({
                "event": analysis["event"],
                "sport": analysis["sport"],
                "commence_time": analysis["commence_time"],
                "implied_prob_sum": round(analysis["implied_prob_sum"], 4),
                "arbitrage": analysis["arbitrage"],
                "profit": round(analysis["profit"], 2) if analysis["profit"] is not None else None,
                "roi": round(analysis["roi"], 2) if analysis["roi"] is not None else None,
                "outcome": row["outcome"],
                "bookmaker": row["bookmaker"],
                "american_odds": row["american_odds"],
                "decimal_odds": round(row["decimal_odds"], 4),
                "stake": round(row["stake"], 2) if "stake" in row else None,
            })

    return pd.DataFrame(rows)


def export_to_csv(filename, analyses):
    df = analyses_to_dataframe(analyses)
    df.to_csv(filename, index=False)
    return df