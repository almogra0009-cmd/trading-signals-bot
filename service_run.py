"""Entry point used by the Windows Scheduled Task.

Runs the bot headless (via pythonw, no console window). Because there is no
console to print to, this configures a rotating file log BEFORE importing the
bot, then hands off to main.main(). Logs go to bot.log next to this file.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Always operate from the project directory regardless of where the task runs.
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# Configure root logging to a rotating file. Doing this before importing main
# means main.py's logging.basicConfig() becomes a no-op (root already has a
# handler), so all bot logs land in the file instead of a non-existent console.
handler = RotatingFileHandler(
    os.path.join(HERE, "bot.log"),
    maxBytes=2_000_000,
    backupCount=3,
    encoding="utf-8",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
)
root = logging.getLogger()
root.setLevel(logging.INFO)
root.addHandler(handler)

# Run with no extra CLI args so main() starts the 15-minute scheduler.
sys.argv = [sys.argv[0]]

import main  # noqa: E402  (import after logging is configured on purpose)

if __name__ == "__main__":
    logging.getLogger("bot").info("Bot started via Windows Scheduled Task (headless).")
    main.main()
