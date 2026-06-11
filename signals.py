"""Signal generation: combine RSI, MACD and (optionally) news sentiment."""
import logging
from dataclasses import dataclass
from typing import Optional

import config
import indicators
from data_fetch import fetch_history
from sentiment import analyze_sentiment

log = logging.getLogger(__name__)


@dataclass
class Signal:
    symbol: str
    name: str
    direction: str           # "BUY" or "SELL"
    price: float             # entry / current price
    stop_loss: float
    target1: float
    target2: float
    rsi: float
    macd_hist: float
    sentiment_score: float
    sentiment_label: str
    volume_ratio: float
    reasons: list


def _round(symbol: str, value: float) -> float:
    """Round to a sensible number of decimals based on price magnitude."""
    if value >= 1000:
        return round(value, 2)
    if value >= 1:
        return round(value, 2)
    return round(value, 6)


def analyze_symbol(symbol: str) -> Optional[Signal]:
    """Run the full analysis for one symbol and return a Signal or None."""
    df = fetch_history(symbol, config.BAR_INTERVAL, config.LOOKBACK_PERIOD)
    if df.empty or len(df) < config.MACD_SLOW + config.MACD_SIGNAL + 5:
        log.info("%s: not enough data, skipping", symbol)
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    rsi_series = indicators.rsi(close, config.RSI_PERIOD)
    macd_line, signal_line, hist = indicators.macd(
        close, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL
    )
    atr_series = indicators.atr(high, low, close, config.ATR_PERIOD)
    vol_ratio_series = indicators.volume_ratio(volume, config.VOLUME_AVG_PERIOD)

    # Latest and previous values
    price = float(close.iloc[-1])
    rsi_now = float(rsi_series.iloc[-1])
    hist_now = float(hist.iloc[-1])
    hist_prev = float(hist.iloc[-2])
    atr_now = float(atr_series.iloc[-1])
    vol_ratio = float(vol_ratio_series.iloc[-1])

    if any(v != v for v in (price, rsi_now, hist_now, atr_now)):  # NaN guard
        log.info("%s: indicators not ready (NaN)", symbol)
        return None

    # MACD momentum: histogram crossing zero is a momentum flip
    macd_bull = hist_now > 0 and hist_prev <= 0
    macd_bear = hist_now < 0 and hist_prev >= 0

    # Sentiment is mandatory for a high-conviction setup.
    if config.USE_SENTIMENT:
        sent_score, sent_label, n_news = analyze_sentiment(symbol)
    else:
        sent_score, sent_label, n_news = 0.0, "neutral", 0

    # Volume confirmation: the current bar must trade well above its average.
    # VOLUME_SPIKE_PCT is "percent above average", so 150 -> ratio of 2.5.
    # Some feeds (e.g. yfinance intraday indices/crypto) report 0 or NaN volume;
    # in that case we simply can't confirm a spike, so the setup doesn't qualify.
    vol_threshold = 1.0 + config.VOLUME_SPIKE_PCT / 100.0
    vol_valid = vol_ratio == vol_ratio and vol_ratio > 0  # not NaN, has data
    volume_ok = vol_valid and vol_ratio >= vol_threshold
    above_avg_pct = (vol_ratio - 1.0) * 100.0 if vol_valid else 0.0

    reasons = []
    direction = None

    # High-conviction setups only: RSI, MACD, sentiment AND volume must ALL
    # agree. No partial / vote-based signals get through.
    buy_ready = (
        rsi_now <= config.RSI_OVERSOLD
        and hist_now > 0
        and config.USE_SENTIMENT
        and sent_label == "positive"
        and volume_ok
    )
    sell_ready = (
        rsi_now >= config.RSI_OVERBOUGHT
        and hist_now < 0
        and config.USE_SENTIMENT
        and sent_label == "negative"
        and volume_ok
    )

    if buy_ready:
        direction = "BUY"
        reasons = [
            f"RSI {rsi_now:.1f} deeply oversold (<= {config.RSI_OVERSOLD:g})",
            "MACD bullish crossover" if macd_bull else "MACD bullish (histogram > 0)",
            f"News sentiment positive ({sent_score:+.2f}, {n_news} items)",
            f"Volume {above_avg_pct:.0f}% above average (>= {config.VOLUME_SPIKE_PCT:g}%)",
        ]
    elif sell_ready:
        direction = "SELL"
        reasons = [
            f"RSI {rsi_now:.1f} deeply overbought (>= {config.RSI_OVERBOUGHT:g})",
            "MACD bearish crossover" if macd_bear else "MACD bearish (histogram < 0)",
            f"News sentiment negative ({sent_score:+.2f}, {n_news} items)",
            f"Volume {above_avg_pct:.0f}% above average (>= {config.VOLUME_SPIKE_PCT:g}%)",
        ]

    if direction is None:
        return None

    # ---- Risk levels from ATR ----
    risk = atr_now * config.ATR_STOP_MULT
    if risk <= 0:
        return None

    if direction == "BUY":
        stop_loss = price - risk
        target1 = price + risk * config.TARGET1_R
        target2 = price + risk * config.TARGET2_R
    else:  # SELL
        stop_loss = price + risk
        target1 = price - risk * config.TARGET1_R
        target2 = price - risk * config.TARGET2_R

    return Signal(
        symbol=symbol,
        name=config.display_name(symbol),
        direction=direction,
        price=_round(symbol, price),
        stop_loss=_round(symbol, stop_loss),
        target1=_round(symbol, target1),
        target2=_round(symbol, target2),
        rsi=round(rsi_now, 1),
        macd_hist=round(hist_now, 4),
        sentiment_score=sent_score,
        sentiment_label=sent_label,
        volume_ratio=round(vol_ratio, 2),
        reasons=reasons,
    )
