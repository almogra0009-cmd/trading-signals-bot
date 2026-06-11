"""Technical indicators implemented with pandas (no TA-Lib dependency)."""
import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    # When there are no losses RSI is 100; when no gains RSI is 0.
    out = out.where(avg_loss != 0, 100.0)
    out = out.where(avg_gain != 0, out)
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """Current volume relative to its rolling average.

    A value of 1.0 means volume equals the trailing average; 2.5 means the
    current bar traded 150% above average. The current bar is excluded from
    the average so a spike doesn't dilute its own baseline.
    """
    avg = volume.shift(1).rolling(window=period, min_periods=period).mean()
    return volume / avg


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range using Wilder's smoothing."""
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
