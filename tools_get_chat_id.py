"""Helper: print the chat id(s) that have messaged your bot.

1. Put your TELEGRAM_BOT_TOKEN in .env
2. Open Telegram, find your bot, and send it any message (e.g. "hi")
3. Run:  python tools_get_chat_id.py
4. Copy the chat id into TELEGRAM_CHAT_ID in .env
"""
import requests

import config

if not config.TELEGRAM_BOT_TOKEN:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env first.")

url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
resp = requests.get(url, timeout=20)
data = resp.json()

if not data.get("ok"):
    raise SystemExit(f"Telegram error: {data}")

updates = data.get("result", [])
if not updates:
    print("No messages found. Send your bot a message first, then re-run.")
else:
    seen = {}
    for upd in updates:
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat", {})
        if chat.get("id") is not None:
            seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name", "")
    for chat_id, name in seen.items():
        print(f"chat_id = {chat_id}   ({name})")
