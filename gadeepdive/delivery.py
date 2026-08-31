"""Report delivery channels. Telegram only, stdlib `urllib` — no third-party
deps, no metered API keys (golden rule). Credentials come from
`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` env vars, never hardcoded.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Callable, Optional

TELEGRAM_API_BASE = "https://api.telegram.org"
TELEGRAM_MESSAGE_LIMIT = 4096


class DeliveryError(RuntimeError):
    """Raised when a delivery attempt fails: missing credentials, or the
    channel's API rejected/failed the send."""


def _telegram_credentials():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise DeliveryError("missing TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID environment variables")
    return token, chat_id


def _chunk_text(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT):
    for i in range(0, len(text), limit):
        yield text[i : i + limit]


def _post_json(url: str, payload: dict, opener: Callable) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with opener(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise DeliveryError(f"Telegram request failed: {exc}") from exc


def deliver_telegram(text: str, opener: Optional[Callable] = None) -> None:
    """Send `text` to Telegram, chunked under the 4096-char message limit.

    Raises `DeliveryError` on missing credentials or a rejected/failed send.
    """
    token, chat_id = _telegram_credentials()
    opener = opener or urllib.request.urlopen
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    for chunk in _chunk_text(text):
        body = _post_json(url, {"chat_id": chat_id, "text": chunk}, opener)
        if not body.get("ok"):
            raise DeliveryError(f"Telegram API rejected the message: {body}")


DELIVERY_SENDERS = {"telegram": deliver_telegram}


def deliver(channel: str, text: str) -> None:
    """Dispatch `text` to the named delivery channel. Raises `DeliveryError`
    for an unknown channel or a failed send."""
    try:
        sender = DELIVERY_SENDERS[channel]
    except KeyError:
        raise DeliveryError(f"unknown delivery channel '{channel}' — expected one of {sorted(DELIVERY_SENDERS)}") from None
    sender(text)
