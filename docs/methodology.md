# Methodology

How the analyzer turns raw bookmaker prices into arbitrage and +EV
opportunities, and the data-quality rules that keep it from reporting
opportunities that do not really exist.

- [1. Odds and implied probability](#1-odds-and-implied-probability)
- [2. The bookmaker margin](#2-the-bookmaker-margin)
- [3. Arbitrage](#3-arbitrage)
- [4. Line-based markets](#4-line-based-markets-spreads-and-totals)
- [5. Market completeness](#5-market-completeness)
- [6. Positive expected value (+EV)](#6-positive-expected-value-ev)
- [7. Execution filters](#7-execution-filters)
- [8. Known limitations](#8-known-limitations)

---

## 1. Odds and implied probability

All calculations use **decimal odds**: the total amount returned per 1 unit
staked, including the stake. A price of 2.50 returns 2.50 on a winning 1.00 bet.

American odds, used by US books and by The Odds API, are converted first
(`analyzer/odds.py`):

| American | Rule | Decimal |
|---|---|---|
| +150 | `1 + 150/100` | 2.50 |
| −110 | `1 + 100/110` | 1.909 |

The **implied probability** of a price is the break-even win rate:

```
p = 1 / d          e.g. 1 / 2.50 = 40%
```

## 2. The bookmaker margin

For a single bookmaker, implied probabilities across all outcomes sum to more
than 100%. The excess is the bookmaker's margin (the "overround" or "vig"):

```
Both sides at −110 (1.909):   1/1.909 + 1/1.909 = 1.0476   → 4.76% margin
```

This sum is the **market efficiency** shown in the dashboard. Lower is better
for the bettor, and the analyzer ranks markets by it even when no arbitrage
exists ("closest to arbitrage").

## 3. Arbitrage

Take the **best** decimal price `dᵢ` for each outcome `i`, each possibly at a
different bookmaker. Define

```
S = Σ 1/dᵢ
```

If `S < 1`, staking every outcome guarantees a profit.

**Stake sizing.** With budget `B`, stake each outcome in proportion to its
implied probability:

```
stakeᵢ = B · (1/dᵢ) / S
```

Then every outcome pays the same amount:

```
payoutᵢ = stakeᵢ · dᵢ = B / S
```

So the guaranteed profit and return are:

```
profit = B/S − B          ROI = 1/S − 1
```

**Example** (demo data, Nuggets @ Lakers, B = $100):

```
Lakers   2.26   (Betsson)   1/2.26   = 0.4425
Nuggets  1.8475 (Bet365)    1/1.8475 = 0.5413
                                   S = 0.9838

stakes   100 · 0.4425/0.9838 = $44.98     100 · 0.5413/0.9838 = $55.02
payout   44.98 · 2.26 = $101.65           55.02 · 1.8475 = $101.65
ROI      1/0.9838 − 1 = 1.65%
```

Implementation: `analyzer/arbitrage.py` (`calculate_stakes`,
`calculate_profit`, `calculate_roi`, `analyze_event`).

## 4. Line-based markets (spreads and totals)

A spread or total bet is defined by its **line** as well as its side. Books
often post different lines for the same game:

```
Book A:  Lakers −3.5 @ 2.10    Nuggets +3.5 @ 1.67
Book B:  Lakers −4.5 @ 2.30    Nuggets +4.5 @ 1.62
```

Lakers −4.5 and Nuggets +3.5 are **not** opposite sides of one bet. If the
Lakers win by exactly 4, both lose. A naive "best price per outcome" search
would combine them anyway.

The analyzer groups outcomes into complementary lines before doing any maths:

| Market | Pairs | Line key |
|---|---|---|
| Spreads | Home −x with Away +x | the home team's point |
| Totals | Over x with Under x | the total |

Each complete line is evaluated independently, and the line with the lowest `S`
is reported. This both prevents false positives from mixed lines and finds real
arbitrage on one line even when other books post different ones.

Implementation: `_group_into_lines` in `analyzer/arbitrage.py`.

## 5. Market completeness

An arbitrage must cover **every** possible result. If the draw is missing from
a soccer match, Home + Away alone can easily sum below 1, but the "guaranteed"
profit becomes a loss whenever the match is drawn.

Rules (`_expected_outcome_count`):

- A line market must have both sides.
- A moneyline must have as many outcomes as the most complete single bookmaker lists.
- A soccer moneyline always needs 3 outcomes (Home, Draw, Away), even if every
  remaining book omits the draw after filtering.

Markets that fail the check are skipped, not reported.

## 6. Positive expected value (+EV)

Arbitrage is rare. A more common edge is a single price that is **higher than
the outcome's true probability justifies**.

**Fair probability.** Pinnacle is widely regarded as the sharpest bookmaker:
low margins, high limits and prices driven by professional bettors. Its prices,
with the margin removed, are a good estimate of the true probabilities. The margin
is removed proportionally ("de-vigging"):

```
fairᵢ = (1/dᵢ) / Σⱼ (1/dⱼ)          using Pinnacle's prices
```

**Expected value** of betting outcome `i` at another book's price `d`:

```
EV = d · fairᵢ − 1
```

Example: Pinnacle has both sides at −110, so the fair probability is 50%
each. Another book offers +110 (2.10) on one side:

```
EV = 2.10 · 0.50 − 1 = +5%
```

As with arbitrage, spread and total prices are only compared with Pinnacle's
price **on the same line**.

Implementation: `analyzer/ev.py`.

## 7. Execution filters

An opportunity is only real if every leg can actually be placed. Before any
analysis, `analyzer/filters.py` removes bookmakers in two passes:

1. **Accessibility ("I bet from…")** keeps only books available from one
   location (Brazil, USA, UK or Europe presets). An arbitrage whose legs need
   accounts in two countries is not one you can take.
2. **Reliability** always removes books whose API feed is known to differ from
   what customers actually see. For example, 1xBet runs many regional sites with
   independent prices, so its feed price is often not available to you. The
   demo data includes one such "too good to be true" 1xBet price to show this
   filter at work.

Bookmaker names are matched in normalised form (lowercase, letters and digits
only), so the pattern `marathonbet` matches the title "Marathon Bet".

## 8. Known limitations

These are documented rather than hidden, and several are on the roadmap:

- **Timing risk.** Prices can move between the scan and placing each leg.
- **Stake limits and account restrictions.** Bookmakers limit or close accounts
  that consistently take arbitrage. Maximum stakes are not modelled.
- **Exchange commission.** Betting exchanges charge commission on winnings,
  which reduces the effective price. Not yet modelled.
- **Stale prices.** Each bookmaker reports a `last_update` time; flagging old
  prices is planned.
- **Rounding.** Bookmakers round stakes and odds. A 0.3% arbitrage can
  disappear after rounding stakes to whole currency units.
