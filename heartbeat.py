"""Send a daily heartbeat summary to Telegram.

Confirms the bot is alive, lists the symbols it watches, and reports how many
signals were sent today. The "signals sent today" figure is read from the
state.json that the scan workflow maintains (restored from the Actions cache).
"""
import json
import os
from datetime import date

import config
import telegram_bot

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


def signals_sent_today() -> int:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    at = data.get("alerts_today") or {}
    if at.get("date") == date.today().isoformat():
        return int(at.get("count", 0))
    return 0


def main():
    count = signals_sent_today()
    symbols = config.WATCHLIST
    text = "\n".join([
        "🫀 <b>Daily heartbeat</b>",
        f"📅 {date.today().isoformat()}",
        "",
        "✅ Bot is alive and scanning every 15 min.",
        f"👀 Symbols scanned: <b>{len(symbols)}</b> — {', '.join(symbols)}",
        f"📤 Signals sent today: <b>{count}</b> (cap {config.MAX_ALERTS_PER_DAY}/day)",
        "",
        "<i>Runs in the cloud via GitHub Actions.</i>",
    ])
    ok = telegram_bot.send_message(text)
    print("Heartbeat sent." if ok else "Heartbeat FAILED — check token / chat id.")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
