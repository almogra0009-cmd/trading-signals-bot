"""Trading signals bot — scans a watchlist on a schedule and alerts to Telegram.

Run:  python main.py            # start the scheduler (scans every N minutes)
      python main.py --once     # run a single scan now and exit
      python main.py --test     # send a test message to Telegram and exit
"""
import argparse
import logging
import sys
import time
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

import config
import telegram_bot
from signals import analyze_symbol

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bot")

# Remembers the last time we alerted on a given (symbol, direction) so we don't
# spam the same setup every 15 minutes.
_last_alert = {}

# Tracks how many alerts we've sent today so we can enforce the daily cap.
_alerts_today = {"date": None, "count": 0}


def _cooldown_active(symbol: str, direction: str) -> bool:
    key = (symbol, direction)
    last = _last_alert.get(key)
    if last is None:
        return False
    elapsed_min = (time.time() - last) / 60.0
    return elapsed_min < config.ALERT_COOLDOWN_MINUTES


def _daily_cap_reached() -> bool:
    """True once we've hit MAX_ALERTS_PER_DAY for the current calendar day."""
    today = date.today()
    if _alerts_today["date"] != today:
        _alerts_today["date"] = today
        _alerts_today["count"] = 0
    return _alerts_today["count"] >= config.MAX_ALERTS_PER_DAY


def scan_once():
    log.info("=== Scan started: %s ===", ", ".join(config.WATCHLIST))
    found = 0
    for symbol in config.WATCHLIST:
        try:
            sig = analyze_symbol(symbol)
        except Exception as exc:
            log.exception("Error analyzing %s: %s", symbol, exc)
            continue

        if sig is None:
            log.info("%s: no signal", symbol)
            continue

        if _cooldown_active(sig.symbol, sig.direction):
            log.info("%s: %s signal in cooldown, skipping alert", sig.symbol, sig.direction)
            continue

        if _daily_cap_reached():
            log.info(
                "%s: %s setup found but daily cap of %d alerts reached, skipping",
                sig.symbol, sig.direction, config.MAX_ALERTS_PER_DAY,
            )
            continue

        log.info(
            "%s: %s @ %s | SL %s T1 %s T2 %s",
            sig.symbol, sig.direction, sig.price, sig.stop_loss, sig.target1, sig.target2,
        )
        if telegram_bot.send_signal(sig):
            _last_alert[(sig.symbol, sig.direction)] = time.time()
            _alerts_today["count"] += 1
            found += 1

    log.info("=== Scan finished: %d alert(s) sent ===", found)


def main():
    parser = argparse.ArgumentParser(description="Trading signals bot")
    parser.add_argument("--once", action="store_true", help="run a single scan and exit")
    parser.add_argument("--test", action="store_true", help="send a Telegram test message and exit")
    args = parser.parse_args()

    if args.test:
        ok = telegram_bot.send_message("✅ Trading signals bot is connected and working.")
        print("Test message sent." if ok else "Failed — check TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID.")
        sys.exit(0 if ok else 1)

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.warning("Telegram is not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    if args.once:
        scan_once()
        return

    # Run one scan immediately, then on a schedule.
    scan_once()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scan_once,
        "interval",
        minutes=config.SCAN_INTERVAL_MINUTES,
        id="scan",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    log.info("Scheduler started — scanning every %d minute(s). Press Ctrl+C to stop.",
             config.SCAN_INTERVAL_MINUTES)
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
