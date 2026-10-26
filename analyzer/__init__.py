"""Market Inefficiency Analyzer: detect arbitrage and +EV bets across sportsbooks.

Modules:
    odds       odds-format conversion and implied probability
    arbitrage  best-price extraction, line grouping and arbitrage analysis
    ev         +EV detection against Pinnacle's de-vigged line
    export     DataFrame / CSV export of analyses
    providers  pluggable odds data sources
    cli        command-line scanner (`python -m analyzer`)
"""

__version__ = "1.0.0"
