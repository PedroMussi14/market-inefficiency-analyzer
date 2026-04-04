# Market Inefficiency Analyzer

A Python-based application that detects pricing inefficiencies across sportsbooks by analyzing live odds data and identifying potential arbitrage opportunities.

## Overview

This project connects to a real-time odds API, extracts betting market data, compares prices across multiple bookmakers, and evaluates whether arbitrage opportunities exist.

Even when no arbitrage is found, the system ranks markets closest to inefficiency based on implied probability.

## Features

- Live odds data via API
- American → Decimal odds conversion
- Best price selection across bookmakers
- Arbitrage detection using implied probability
- ROI and profit calculation
- Ranking of closest-to-arbitrage markets
- Streamlit dashboard for visualization
- CSV export for analysis

## Tech Stack

- Python
- pandas
- Streamlit
- requests

## How It Works

For each event:
1. Extract odds from all bookmakers
2. Select best odds per outcome
3. Convert to decimal format
4. Compute implied probability:

   sum(1 / odds)

5. If result < 1 → arbitrage exists

## How to Run

1. Clone the repo:

```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo