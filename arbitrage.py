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


def get_best_odds_for_event(event, selected_market="h2h"):
    best_odds = {}

    for bookmaker in event.get("bookmakers", []):
        book_title = bookmaker.get("title", bookmaker.get("key", "Unknown"))

        for market in bookmaker.get("markets", []):
            if market.get("key") not in ["h2h", "spreads", "totals"]:
                continue

            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                american_price = outcome["price"]
                decimal_price = american_to_decimal(american_price)

                link = outcome.get("link") or market.get("link") or bookmaker.get("link")

                if name not in best_odds or decimal_price > best_odds[name]["odds"]:
                    best_odds[name] = {
                        "bookmaker": book_title,
                        "american_odds": american_price,
                        "odds": decimal_price,
                        "link": link,
                    }

    return best_odds


def analyze_event(event, bankroll=100):
    best_odds = get_best_odds_for_event(event, selected_market="h2h")

    if len(best_odds) < 2:
        return None

    outcome_names = list(best_odds.keys())
    decimal_odds = [best_odds[name]["odds"] for name in outcome_names]
    implied_prob_sum = sum(1 / odd for odd in decimal_odds)
    arb_exists = is_arbitrage(decimal_odds)

    results = []
    for name in outcome_names:
        results.append({
            "outcome": name,
            "bookmaker": best_odds[name]["bookmaker"],
            "american_odds": best_odds[name]["american_odds"],
            "decimal_odds": best_odds[name]["odds"],
            "link": best_odds[name].get("link")   # ← NEW: Add link to each result
        })

    analysis = {
        "event": f"{event.get('away_team')} vs {event.get('home_team')}",
        "sport": event.get("sport_title"),
        "commence_time": event.get("commence_time"),
        "implied_prob_sum": implied_prob_sum,
        "arbitrage": arb_exists,
        "results": results,
    }

    if arb_exists:
        stakes = calculate_stakes(bankroll, decimal_odds)
        profit = calculate_profit(bankroll, stakes, decimal_odds)
        roi = calculate_roi(bankroll, profit)

        for i in range(len(results)):
            results[i]["stake"] = stakes[i]

        analysis["profit"] = profit
        analysis["roi"] = roi
    else:
        analysis["profit"] = None
        analysis["roi"] = None

    return analysis