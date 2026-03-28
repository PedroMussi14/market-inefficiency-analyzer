def is_arbitrage(odds):
    return sum(1/o for o in odds) < 1


def calculate_stakes(bankroll, odds):
    inv_sum = sum(1/o for o in odds)
    stakes = [(bankroll * (1/o) / inv_sum) for o in odds]
    return stakes


def calculate_profit(bankroll, stakes, odds):
    returns = [stake * odd for stake, odd in zip(stakes, odds)]
    return min(returns) - bankroll