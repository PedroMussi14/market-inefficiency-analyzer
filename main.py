from api_client import get_odds
from arbitrage import analyze_event
from exporter import export_to_csv


def print_divider():
    print("-" * 90)


def print_event(analysis):
    print(f"Event: {analysis['event']}")
    print(f"Sport: {analysis['sport']}")
    print(f"Start Time: {analysis['commence_time']}")
    print(f"Implied Probability Sum: {analysis['implied_prob_sum']:.4f}")
    print(f"Status: {'Arbitrage Found' if analysis['arbitrage'] else 'No Arbitrage'}")
    print()

    for row in analysis["results"]:
        line = (
            f"Outcome: {row['outcome']:<25} "
            f"Bookmaker: {row['bookmaker']:<15} "
            f"American: {row['american_odds']:<8} "
            f"Decimal: {row['decimal_odds']:.4f}"
        )

        if "stake" in row:
            line += f" Stake: ${row['stake']:.2f}"

        print(line)

    if analysis["arbitrage"]:
        print()
        print(f"Guaranteed Profit: ${analysis['profit']:.2f}")
        print(f"ROI: {analysis['roi']:.2f}%")

    print_divider()


def main():
    bankroll = 100
    events = get_odds()

    all_analyses = []

    for event in events:
        analysis = analyze_event(event, bankroll)
        if analysis is not None:
            all_analyses.append(analysis)

    df = export_to_csv("market_analysis_results.csv", all_analyses)
    print("Results exported to market_analysis_results.csv")

    arbitrage_opportunities = [a for a in all_analyses if a["arbitrage"]]
    closest_opportunities = sorted(all_analyses, key=lambda x: x["implied_prob_sum"])

    print_divider()
    print("MARKET INEFFICIENCY ANALYZER")
    print_divider()

    if arbitrage_opportunities:
        print("PROFITABLE ARBITRAGE OPPORTUNITIES")
        print_divider()

        for analysis in sorted(arbitrage_opportunities, key=lambda x: x["roi"], reverse=True):
            print_event(analysis)
    else:
        print("No profitable arbitrage opportunities found.")
        print_divider()

    print("TOP 5 CLOSEST MARKETS TO ARBITRAGE")
    print_divider()

    top_n = min(5, len(closest_opportunities))
    for analysis in closest_opportunities[:top_n]:
        print_event(analysis)

    print("\nPANDAS SUMMARY")
    print(df.head())


if __name__ == "__main__":
    main()