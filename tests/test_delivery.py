import json
import urllib.error

import pytest

from gadeepdive import delivery


class _FakeResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _recording_opener(calls, body=None):
    body = body if body is not None else {"ok": True}

    def opener(request, timeout=15):
        calls.append(request)
        return _FakeResponse(body)

    return opener


def _erroring_opener(request, timeout=15):
    raise urllib.error.URLError("connection refused")


# ---- missing credentials -----------------------------------------------------------


def test_deliver_telegram_missing_both_env_vars_raises(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(delivery.DeliveryError, match="TELEGRAM_BOT_TOKEN"):
        delivery.deliver_telegram("hello")


def test_deliver_telegram_missing_bot_token_raises(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with pytest.raises(delivery.DeliveryError):
        delivery.deliver_telegram("hello")


def test_deliver_telegram_missing_chat_id_raises(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(delivery.DeliveryError):
        delivery.deliver_telegram("hello")


# ---- happy path ---------------------------------------------------------------------


def test_deliver_telegram_happy_path_posts_to_send_message(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    calls = []
    delivery.deliver_telegram("the full report text", opener=_recording_opener(calls))
    assert len(calls) == 1
    request = calls[0]
    assert request.full_url == "https://api.telegram.org/botbot-token/sendMessage"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload == {"chat_id": "12345", "text": "the full report text"}


def test_deliver_telegram_chunks_text_over_the_message_limit(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    calls = []
    long_text = "x" * (delivery.TELEGRAM_MESSAGE_LIMIT + 100)
    delivery.deliver_telegram(long_text, opener=_recording_opener(calls))
    assert len(calls) == 2


# ---- failure paths -------------------------------------------------------------------


def test_deliver_telegram_api_rejection_raises_delivery_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    calls = []
    opener = _recording_opener(calls, body={"ok": False, "description": "chat not found"})
    with pytest.raises(delivery.DeliveryError, match="chat not found"):
        delivery.deliver_telegram("hello", opener=opener)


def test_deliver_telegram_network_error_raises_delivery_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with pytest.raises(delivery.DeliveryError, match="Telegram request failed"):
        delivery.deliver_telegram("hello", opener=_erroring_opener)


# ---- dispatcher -----------------------------------------------------------------------


def test_deliver_dispatches_to_telegram_sender(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    sent = []
    monkeypatch.setitem(delivery.DELIVERY_SENDERS, "telegram", lambda text: sent.append(text))
    delivery.deliver("telegram", "hi there")
    assert sent == ["hi there"]


def test_deliver_unknown_channel_raises_delivery_error():
    with pytest.raises(delivery.DeliveryError, match="unknown delivery channel"):
        delivery.deliver("carrier-pigeon", "hi there")


# ---- send_photo: missing credentials --------------------------------------------------


def test_send_photo_missing_both_env_vars_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(b"not-really-a-png")
    with pytest.raises(delivery.DeliveryError, match="TELEGRAM_BOT_TOKEN"):
        delivery.send_photo(str(image_path), "caption")


def test_send_photo_missing_chat_id_and_home_channel_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(b"not-really-a-png")
    with pytest.raises(delivery.DeliveryError):
        delivery.send_photo(str(image_path), "caption")


def test_send_photo_falls_back_to_home_channel_when_chat_id_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_HOME_CHANNEL", "home-channel-99")
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(b"not-really-a-png")
    calls = []
    delivery.send_photo(str(image_path), "caption", opener=_recording_opener(calls))
    assert len(calls) == 1
    body = calls[0].data.decode("latin-1")
    assert "home-channel-99" in body


# ---- send_photo: happy path -------------------------------------------------------------


def test_send_photo_happy_path_posts_multipart_to_send_photo(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    image_bytes = b"\x89PNG\r\n\x1a\nfake-png-bytes"
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(image_bytes)

    calls = []
    delivery.send_photo(str(image_path), "the caption text", opener=_recording_opener(calls))

    assert len(calls) == 1
    request = calls[0]
    assert request.full_url == "https://api.telegram.org/botbot-token/sendPhoto"
    assert request.headers.get("Content-type", "").startswith("multipart/form-data; boundary=")

    body = request.data
    assert b'name="chat_id"' in body
    assert b"12345" in body
    assert b'name="caption"' in body
    assert b"the caption text" in body
    assert b'name="photo"; filename="dashboard.png"' in body
    assert image_bytes in body


def test_send_photo_api_rejection_raises_delivery_error(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(b"fake-png-bytes")
    calls = []
    opener = _recording_opener(calls, body={"ok": False, "description": "chat not found"})
    with pytest.raises(delivery.DeliveryError, match="chat not found"):
        delivery.send_photo(str(image_path), "caption", opener=opener)


def test_send_photo_network_error_raises_delivery_error(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    image_path = tmp_path / "dashboard.png"
    image_path.write_bytes(b"fake-png-bytes")
    with pytest.raises(delivery.DeliveryError, match="Telegram sendPhoto request failed"):
        delivery.send_photo(str(image_path), "caption", opener=_erroring_opener)
