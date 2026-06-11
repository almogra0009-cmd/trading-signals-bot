"""Configuration loaded from environment / .env file."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name, default=None):
    val = os.getenv(name)
    return val if val not in (None, "") else default


def _get_float(name, default):
    try:
        return float(_get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _get_int(name, default):
    try:
        return int(_get(name, default))
    except (TypeError, ValueError):
        return int(default)


def _get_bool(name, default=False):
    val = _get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ===== Telegram =====
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID")

# ===== Scan settings =====
SCAN_INTERVAL_MINUTES = _get_int("SCAN_INTERVAL_MINUTES", 15)
WATCHLIST = [s.strip() for s in _get("WATCHLIST", "^GSPC,^IXIC,BTC-USD,ETH-USD").split(",") if s.strip()]
BAR_INTERVAL = _get("BAR_INTERVAL", "15m")
LOOKBACK_PERIOD = _get("LOOKBACK_PERIOD", "60d")

# ===== Indicator thresholds =====
# Tightened for high-conviction setups only: RSI must be deeply oversold /
# overbought before we even consider an alert.
RSI_PERIOD = _get_int("RSI_PERIOD", 14)
RSI_OVERSOLD = _get_float("RSI_OVERSOLD", 28)
RSI_OVERBOUGHT = _get_float("RSI_OVERBOUGHT", 72)
MACD_FAST = _get_int("MACD_FAST", 12)
MACD_SLOW = _get_int("MACD_SLOW", 26)
MACD_SIGNAL = _get_int("MACD_SIGNAL", 9)
ATR_PERIOD = _get_int("ATR_PERIOD", 14)

# ===== Volume confirmation =====
# A setup must be backed by a volume surge. VOLUME_SPIKE_PCT is how far above
# the rolling average the current bar's volume must be (150 = 150% above
# average, i.e. 2.5x the average). VOLUME_AVG_PERIOD is the averaging window.
VOLUME_AVG_PERIOD = _get_int("VOLUME_AVG_PERIOD", 20)
VOLUME_SPIKE_PCT = _get_float("VOLUME_SPIKE_PCT", 150)

# ===== Risk / reward =====
ATR_STOP_MULT = _get_float("ATR_STOP_MULT", 1.5)
TARGET1_R = _get_float("TARGET1_R", 1.5)
TARGET2_R = _get_float("TARGET2_R", 3.0)

# ===== Misc =====
# Sentiment confirmation is mandatory for high-conviction setups, so this must
# stay enabled for any alert to fire.
USE_SENTIMENT = _get_bool("USE_SENTIMENT", True)
ALERT_COOLDOWN_MINUTES = _get_int("ALERT_COOLDOWN_MINUTES", 120)
# Hard cap on alerts per calendar day — only the best few setups get through.
MAX_ALERTS_PER_DAY = _get_int("MAX_ALERTS_PER_DAY", 3)

# Friendly display names for common symbols
SYMBOL_NAMES = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq Composite",
    "^NDX": "Nasdaq 100",
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "NVDA": "NVIDIA",
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
}


def display_name(symbol: str) -> str:
    return SYMBOL_NAMES.get(symbol, symbol)
