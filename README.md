# Trading Signals Bot

Scans a watchlist (S&P 500, Nasdaq, Bitcoin, Ethereum by default) every 15 minutes,
pulls **real prices from Yahoo Finance**, analyzes **RSI**, **MACD** and **news
sentiment**, and sends **Telegram alerts** with entry, stop loss, target 1 and
target 2.

> ⚠️ Educational use only. This is not financial advice. Markets are risky.

## What it does

1. Fetches OHLCV candles from Yahoo Finance (`yfinance`).
2. Computes RSI(14), MACD(12/26/9) and ATR(14).
3. Reads recent headlines and scores sentiment with VADER.
4. Generates a **BUY** or **SELL** signal when RSI is stretched **and** at least
   one more indicator confirms (MACD / sentiment).
5. Builds risk levels from ATR:
   - Stop loss = entry ± `ATR × ATR_STOP_MULT`
   - Target 1 = entry ± `risk × TARGET1_R`
   - Target 2 = entry ± `risk × TARGET2_R`
6. Sends a formatted alert to Telegram and respects a per-symbol cooldown so the
   same setup isn't repeated every scan.

## Setup (Windows / PowerShell)

```powershell
cd C:\Projects\TradingBot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Then edit `.env`:

1. **Create a Telegram bot:** open Telegram, message **@BotFather**, send
   `/newbot`, follow the prompts, and copy the token into `TELEGRAM_BOT_TOKEN`.
2. **Get your chat id:** send your new bot any message, then run
   `python tools_get_chat_id.py` and copy the printed id into `TELEGRAM_CHAT_ID`.
3. (Optional) adjust `WATCHLIST`, thresholds and risk multiples.

## Run

```powershell
python main.py --test     # send a test message to confirm Telegram works
python main.py --once     # run a single scan now and print/send any signals
python main.py            # run forever, scanning every SCAN_INTERVAL_MINUTES
```

## Watchlist symbols (Yahoo Finance format)

| Symbol    | Meaning            |
|-----------|--------------------|
| `^GSPC`   | S&P 500 index      |
| `^IXIC`   | Nasdaq Composite   |
| `^NDX`    | Nasdaq 100         |
| `BTC-USD` | Bitcoin            |
| `ETH-USD` | Ethereum           |
| `AAPL`    | Any stock ticker   |

Add as many tickers as you like to `WATCHLIST` (comma-separated). Note that
intraday `15m` data is only available for the trailing ~60 days, and stock
indices only update during US market hours — crypto trades 24/7.

## Files

- `main.py` — scheduler + scan loop + CLI
- `signals.py` — combines indicators + sentiment into a Signal
- `indicators.py` — RSI / MACD / ATR
- `data_fetch.py` — Yahoo Finance price + news
- `sentiment.py` — VADER news sentiment
- `telegram_bot.py` — formats and sends alerts
- `config.py` — reads settings from `.env`
- `tools_get_chat_id.py` — helper to find your Telegram chat id
