from api_client import get_odds
from arbitrage import analyze_event


def print_divider():
    print("-" * 90)


def main():
    bankroll = 100
    events = get_odds()

    opportunities = []

    for event in events:
        analysis = analyze_event(event, bankroll)
        if analysis is not None and analysis["profit"] > 0:
            opportunities.append(analysis)

    opportunities.sort(key=lambda x: x["roi"], reverse=True)

    print_divider()
    print("MARKET INEFFICIENCY ANALYZER")
    print_divider()

    if not opportunities:
        print("No profitable arbitrage opportunities found.")
        print_divider()
        return

    print(f"Found {len(opportunities)} profitable opportunities.")
    print_divider()

    for analysis in opportunities:
        print(f"Event: {analysis['event']}")
        print(f"Sport: {analysis['sport']}")
        print(f"Start Time: {analysis['commence_time']}")
        print()

        for row in analysis["results"]:
            print(
                f"Outcome: {row['outcome']:<25} "
                f"Bookmaker: {row['bookmaker']:<15} "
                f"American: {row['american_odds']:<8} "
                f"Decimal: {row['decimal_odds']:.2f} "
                f"Stake: ${row['stake']:.2f}"
            )

        print()
        print(f"Guaranteed Profit: ${analysis['profit']:.2f}")
        print(f"ROI: {analysis['roi']:.2f}%")
        print_divider()


if __name__ == "__main__":
    main()