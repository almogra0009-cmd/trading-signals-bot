"""CI entry point: run ONE scan with state persisted across runs.

GitHub Actions runs on a fresh machine each time, so the in-memory cooldown
(`_last_alert`) and daily-alert cap (`_alerts_today`) in main.py would reset on
every run. This wrapper restores that state from state.json before the scan and
writes it back afterwards, so ALERT_COOLDOWN_MINUTES and MAX_ALERTS_PER_DAY
keep working across scheduled runs. The workflow caches state.json between runs.

It does not modify main.py — it just imports it and runs a single scan.
"""
import json
import os
import time
from datetime import date

import main

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # Cooldown timestamps were stored as "SYMBOL|DIRECTION" -> epoch seconds.
    last = {}
    for key, ts in data.get("last_alert", {}).items():
        symbol, _, direction = key.rpartition("|")
        last[(symbol, direction)] = float(ts)
    main._last_alert = last

    # Only restore today's count if the saved state is from the current day.
    at = data.get("alerts_today") or {}
    if at.get("date") == date.today().isoformat():
        main._alerts_today = {"date": date.today(), "count": int(at.get("count", 0))}


def save_state():
    last = {f"{sym}|{dirn}": ts for (sym, dirn), ts in main._last_alert.items()}
    at_date = main._alerts_today.get("date")
    payload = {
        "last_alert": last,
        "alerts_today": {
            "date": at_date.isoformat() if hasattr(at_date, "isoformat") else None,
            "count": main._alerts_today.get("count", 0),
        },
        "updated": time.time(),
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


if __name__ == "__main__":
    load_state()
    main.scan_once()
    save_state()
