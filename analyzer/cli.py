# =============================================================================
# cli.py
# Command-line scanner: fetch odds for one sport, report arbitrage
# opportunities and the markets closest to arbitrage, and export CSVs.
#
#   python -m analyzer --sport basketball_nba --market h2h --regions us
#   python -m analyzer --help
# =============================================================================

import argparse
import sys
from pathlib import Path

from .arbitrage import analyze_event
from .export import export_detailed_csv, export_summary_csv
from .providers import PROVIDERS, get_provider

DIVIDER = "-" * 90


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m analyzer",
        description="Scan sportsbook odds for arbitrage opportunities.",
    )
    parser.add_argument("--provider", default="odds_api", choices=sorted(PROVIDERS),
                        help="odds data source (default: %(default)s)")
    parser.add_argument("--sport", default="basketball_nba",
                        help="sport key, e.g. soccer_epl (default: %(default)s)")
    parser.add_argument("--market", default="h2h", choices=["h2h", "spreads", "totals"],
                        help="market type (default: %(default)s)")
    parser.add_argument("--regions", default="us",
                        help="comma-separated bookmaker regions, e.g. eu,uk (default: %(default)s)")
    parser.add_argument("--bankroll", type=float, default=100.0,
                        help="total stake per event used for stake sizing (default: %(default)s)")
    parser.add_argument("--top", type=int, default=5,
                        help="number of closest-to-arbitrage markets to show (default: %(default)s)")
    parser.add_argument("--output-dir", type=Path, default=Path("output"),
                        help="directory for CSV exports (default: %(default)s)")
    return parser.parse_args(argv)


def print_event(analysis: dict) -> None:
    print(f"Event: {analysis['event']}")
    print(f"Sport: {analysis['sport']}")
    print(f"Start Time: {analysis['commence_time']}")
    if analysis.get("line") is not None:
        print(f"Line: {analysis['line']}")
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

    print(DIVIDER)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    provider = get_provider(args.provider)

    if not provider.is_configured():
        print(f"Provider '{args.provider}' is not configured. {provider.setup_help()}",
              file=sys.stderr)
        return 1

    events = provider.get_odds(sport=args.sport, markets=args.market, regions=args.regions)
    analyses = [
        analysis
        for event in events
        if (analysis := analyze_event(event, args.bankroll, selected_market=args.market))
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    export_detailed_csv(args.output_dir / "detailed.csv", analyses)
    export_summary_csv(args.output_dir / "summary.csv", analyses)

    print(DIVIDER)
    print(f"MARKET INEFFICIENCY ANALYZER  ·  {args.sport}  ·  {args.market}  ·  "
          f"{len(analyses)} events analysed")
    print(DIVIDER)

    arbitrage = sorted((a for a in analyses if a["arbitrage"]),
                       key=lambda a: a["roi"], reverse=True)
    if arbitrage:
        print("PROFITABLE ARBITRAGE OPPORTUNITIES")
        print(DIVIDER)
        for analysis in arbitrage:
            print_event(analysis)
    else:
        print("No profitable arbitrage opportunities found.")
        print(DIVIDER)

    print(f"TOP {args.top} CLOSEST MARKETS TO ARBITRAGE")
    print(DIVIDER)
    for analysis in sorted(analyses, key=lambda a: a["implied_prob_sum"])[:args.top]:
        print_event(analysis)

    print(f"Results exported to {args.output_dir / 'detailed.csv'} "
          f"and {args.output_dir / 'summary.csv'}")
    return 0
