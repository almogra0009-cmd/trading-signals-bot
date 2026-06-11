"""Fetch real market data from Yahoo Finance via yfinance."""
import logging

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def fetch_history(symbol: str, interval: str, period: str) -> pd.DataFrame:
    """Download OHLCV candles for a symbol.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume.
    Returns an empty DataFrame on failure.
    """
    try:
        df = yf.download(
            tickers=symbol,
            interval=interval,
            period=period,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:  # network / parsing errors
        log.warning("Failed to fetch %s: %s", symbol, exc)
        return pd.DataFrame()

    if df is None or df.empty:
        log.warning("No data returned for %s", symbol)
        return pd.DataFrame()

    # yfinance may return a MultiIndex for the columns; flatten it.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()
    return df


def fetch_news(symbol: str, limit: int = 10):
    """Return a list of recent news headlines for a symbol (best effort)."""
    headlines = []
    try:
        ticker = yf.Ticker(symbol)
        items = ticker.news or []
        for item in items[:limit]:
            # yfinance has used a couple of shapes for the news payload.
            content = item.get("content", item)
            title = content.get("title") or item.get("title")
            if title:
                headlines.append(title)
    except Exception as exc:
        log.debug("No news for %s: %s", symbol, exc)
    return headlines
