"""Hourly news watcher — warns 30-90 min before upcoming red-impact news."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from src import news, telegram_notify
from src.formatters import news_warning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("news_watcher")

SEEN_FILE = Path("bot/state/news_seen.json")


def main() -> int:
    log.info("=== News watcher start ===")
    try:
        upcoming = news.upcoming_red_news(within_minutes=90)
    except Exception as e:
        log.error("News fetch failed: %s", e)
        return 1

    if not upcoming:
        log.info("No upcoming red news in next 90 min.")
        return 0

    # Dedupe (don't re-warn for same event)
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

    fresh = [n for n in upcoming if f"{n.title}|{n.date.isoformat()}" not in seen]
    if not fresh:
        log.info("All upcoming already warned.")
        return 0

    text = news_warning(fresh)
    ok = telegram_notify.send(text)
    if ok:
        for n in fresh:
            seen.add(f"{n.title}|{n.date.isoformat()}")
        SEEN_FILE.write_text(json.dumps(list(seen)[-200:], indent=0))
        log.info("Warned for %d events.", len(fresh))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
