"""
Asset and source configuration for the market pipeline.
This file defines the tracked assets for crypto, forex, metals, and news mapping.
"""

CRYPTO_ASSETS = [
    {
        "symbol": "bitcoin",
        "display_symbol": "BTC/USD",
        "name": "Bitcoin",
        "market_type": "crypto",
        "source": "coingecko",
        "vs_currency": "usd",
    },
    {
        "symbol": "ethereum",
        "display_symbol": "ETH/USD",
        "name": "Ethereum",
        "market_type": "crypto",
        "source": "coingecko",
        "vs_currency": "usd",
    },
]

FOREX_ASSETS = [
    {
        "symbol": "EURUSD",
        "display_symbol": "EUR/USD",
        "name": "Euro / US Dollar",
        "market_type": "forex",
        "source": "exchangerate",
        "base_currency": "EUR",
        "quote_currency": "USD",
    },
    {
        "symbol": "GBPUSD",
        "display_symbol": "GBP/USD",
        "name": "British Pound / US Dollar",
        "market_type": "forex",
        "source": "exchangerate",
        "base_currency": "GBP",
        "quote_currency": "USD",
    },
]

METALS_ASSETS = [
    {
        "symbol": "GC=F",
        "display_symbol": "XAU/USD",
        "name": "Gold / US Dollar",
        "market_type": "metals",
        "source": "yfinance",
        "base_asset": "XAU",
        "quote_currency": "USD",
    },
    {
        "symbol": "SI=F",
        "display_symbol": "XAG/USD",
        "name": "Silver / US Dollar",
        "market_type": "metals",
        "source": "yfinance",
        "base_asset": "XAG",
        "quote_currency": "USD",
    },
]

NEWS_TARGETS = [
    {
        "symbol": "BTC/USD",
        "display_symbol": "BTC/USD",
        "market_type": "crypto",
        "source": "finnhub",
        "keywords": ["bitcoin", "btc", "crypto market"],
    },
    {
        "symbol": "ETH/USD",
        "display_symbol": "ETH/USD",
        "market_type": "crypto",
        "source": "finnhub",
        "keywords": ["ethereum", "eth"],
    },
    {
        "symbol": "EUR/USD",
        "display_symbol": "EUR/USD",
        "market_type": "forex",
        "source": "finnhub",
        "keywords": ["eur usd", "euro dollar", "ecb", "euro"],
    },
    {
        "symbol": "GBP/USD",
        "display_symbol": "GBP/USD",
        "market_type": "forex",
        "source": "finnhub",
        "keywords": ["gbp usd", "pound dollar", "boe", "british pound"],
    },
    {
        "symbol": "XAU/USD",
        "display_symbol": "XAU/USD",
        "market_type": "metals",
        "source": "finnhub",
        "keywords": ["gold", "xau", "gold price"],
    },
    {
        "symbol": "XAG/USD",
        "display_symbol": "XAG/USD",
        "market_type": "metals",
        "source": "finnhub",
        "keywords": ["silver", "xag", "silver price"],
    },
]

ALL_MARKET_ASSETS = CRYPTO_ASSETS + FOREX_ASSETS + METALS_ASSETS