"""Minimal Telegram sender using the Bot API over HTTP."""
import logging

import requests

import config
from signals import Signal

log = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _escape(text: str) -> str:
    """Escape characters that break Telegram HTML parse mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_signal(sig: Signal) -> str:
    arrow = "🟢" if sig.direction == "BUY" else "🔴"
    reasons = "\n".join(f"  • {_escape(r)}" for r in sig.reasons)
    sentiment_line = (
        f"📰 Sentiment: {sig.sentiment_label} ({sig.sentiment_score:+.2f})\n"
        if config.USE_SENTIMENT else ""
    )
    return (
        f"{arrow} <b>{sig.direction} signal — {_escape(sig.name)}</b> "
        f"(<code>{_escape(sig.symbol)}</code>)\n"
        f"\n"
        f"💵 Entry: <b>{sig.price}</b>\n"
        f"🛑 Stop loss: {sig.stop_loss}\n"
        f"🎯 Target 1: {sig.target1}\n"
        f"🎯 Target 2: {sig.target2}\n"
        f"\n"
        f"📊 RSI: {sig.rsi} | MACD hist: {sig.macd_hist}\n"
        f"🔊 Volume: {sig.volume_ratio}x avg ({(sig.volume_ratio - 1) * 100:+.0f}%)\n"
        f"{sentiment_line}"
        f"\n"
        f"<b>Why:</b>\n{reasons}\n"
        f"\n"
        f"<i>Not financial advice. For educational use only.</i>"
    )


def send_message(text: str) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.error("Telegram token / chat id not configured — cannot send alert.")
        return False
    try:
        resp = requests.post(
            API_URL.format(token=config.TELEGRAM_BOT_TOKEN),
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            log.error("Telegram API error %s: %s", resp.status_code, resp.text)
            return False
        return True
    except requests.RequestException as exc:
        log.error("Failed to send Telegram message: %s", exc)
        return False


def send_signal(sig: Signal) -> bool:
    return send_message(format_signal(sig))
