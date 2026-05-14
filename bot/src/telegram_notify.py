"""Telegram messenger — uses creds from config.py (env vars override)."""
from __future__ import annotations

import logging

import requests

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)


def send(text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("Telegram credentials missing in config.py")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }, timeout=20)
        if r.status_code != 200:
            log.error("Telegram error %s: %s", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        log.error("Telegram send failed: %s", e)
        return False
