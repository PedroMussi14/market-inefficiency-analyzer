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


def _outcome_key(outcome, selected_market):
    """
    Build a stable key per betting outcome.

    For spreads/totals, line ("point") must be part of the key or we can
    accidentally combine incompatible lines and report false arbitrage.
    """
    name = outcome["name"]
    point = outcome.get("point")

    if selected_market in {"spreads", "totals"}:
        return f"{name}|{point}", name, point

    return name, name, point


def get_best_odds_for_event(event, selected_market="h2h"):
    best_odds = {}

    for bookmaker in event.get("bookmakers", []):
        book_title = bookmaker.get("title", bookmaker.get("key", "Unknown"))

        for market in bookmaker.get("markets", []):
            market_key = market.get("key")
            if market_key != selected_market:
                continue

            for outcome in market.get("outcomes", []):
                outcome_id, name, point = _outcome_key(outcome, selected_market)
                american_price = outcome["price"]
                decimal_price = american_to_decimal(american_price)

                link = outcome.get("link") or market.get("link") or bookmaker.get("link")

                if outcome_id not in best_odds or decimal_price > best_odds[outcome_id]["odds"]:
                    best_odds[outcome_id] = {
                        "outcome_id": outcome_id,
                        "name": name,
                        "point": point,
                        "bookmaker": book_title,
                        "american_odds": american_price,
                        "odds": decimal_price,
                        "link": link,
                    }

    return best_odds


def analyze_event(event, bankroll=100, selected_market="h2h"):
    best_odds = get_best_odds_for_event(event, selected_market=selected_market)

    if len(best_odds) < 2:
        return None

    outcome_ids = list(best_odds.keys())
    decimal_odds = [best_odds[outcome_id]["odds"] for outcome_id in outcome_ids]
    implied_prob_sum = sum(1 / odd for odd in decimal_odds)
    arb_exists = is_arbitrage(decimal_odds)

    results = []
    for outcome_id in outcome_ids:
        results.append({
            "outcome": best_odds[outcome_id]["name"],
            "point": best_odds[outcome_id]["point"],
            "bookmaker": best_odds[outcome_id]["bookmaker"],
            "american_odds": best_odds[outcome_id]["american_odds"],
            "decimal_odds": best_odds[outcome_id]["odds"],
            "link": best_odds[outcome_id].get("link")
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