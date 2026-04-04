def american_to_decimal(american_odds: int) -> float:
    if american_odds > 0:
        return 1 + (american_odds / 100)
    return 1 + (100 / abs(american_odds))


def is_arbitrage(decimal_odds):
    return sum(1 / odd for odd in decimal_odds) < 1


def calculate_stakes(bankroll, odds):
    inverse_sum = sum(1 / odd for odd in odds)
    stakes = [(bankroll / odd) / inverse_sum for odd in odds]
    return stakes


def calculate_profit(bankroll, stakes, odds):
    payouts = [stake * odd for stake, odd in zip(stakes, odds)]
    guaranteed_payout = min(payouts)
    return guaranteed_payout - bankroll


def calculate_roi(bankroll, profit):
    return (profit / bankroll) * 100


def get_best_odds_for_event(event):
    """
    Extracts the best available odds for each outcome across all bookmakers.
    Works for both 2-outcome and 3-outcome markets.
    """
    best_odds = {}

    bookmakers = event.get("bookmakers", [])
    if not bookmakers:
        return {}

    for bookmaker in bookmakers:
        book_title = bookmaker.get("title", bookmaker.get("key", "Unknown"))

        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue

            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                american_price = outcome["price"]
                decimal_price = american_to_decimal(american_price)

                if name not in best_odds or decimal_price > best_odds[name]["odds"]:
                    best_odds[name] = {
                        "bookmaker": book_title,
                        "american_odds": american_price,
                        "odds": decimal_price,
                    }

    return best_odds


def analyze_event(event, bankroll=100):
    best_odds = get_best_odds_for_event(event)

    if len(best_odds) < 2:
        return None

    outcome_names = list(best_odds.keys())
    decimal_odds = [best_odds[name]["odds"] for name in outcome_names]

    implied_prob_sum = sum(1 / odd for odd in decimal_odds)

    print(f"\nChecking event: {event.get('away_team')} vs {event.get('home_team')}")
    print("Best odds found:")
    for name in outcome_names:
        print(
            f"  {name}: {best_odds[name]['odds']:.4f} "
            f"at {best_odds[name]['bookmaker']}"
        )
        
    print(f"Implied probability sum: {implied_prob_sum:.4f}")
    if not is_arbitrage(decimal_odds):
        return None

    stakes = calculate_stakes(bankroll, decimal_odds)
    profit = calculate_profit(bankroll, stakes, decimal_odds)
    roi = calculate_roi(bankroll, profit)

    results = []
    for name, stake in zip(outcome_names, stakes):
        results.append({
            "outcome": name,
            "bookmaker": best_odds[name]["bookmaker"],
            "american_odds": best_odds[name]["american_odds"],
            "decimal_odds": best_odds[name]["odds"],
            "stake": stake,
        })

    return {
        "event": f"{event.get('away_team')} vs {event.get('home_team')}",
        "sport": event.get("sport_title"),
        "commence_time": event.get("commence_time"),
        "profit": profit,
        "roi": roi,
        "results": results,
    }