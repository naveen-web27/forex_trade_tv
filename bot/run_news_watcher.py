"""Hourly news watcher — warns 30-90 min before upcoming red-impact news."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytz

from src import news, telegram_notify, sheets_sync
from src.config import CFG
from src.formatters import news_warning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("news_watcher")

SEEN_FILE = Path("bot/state/news_seen.json")

# Currencies covered by the dashboard's macro/news view.
RELEVANT_COUNTRIES = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"}


def _sync_calendar_to_sheet() -> None:
    """Push this week's high/medium-impact events so the dashboard can show upcoming news per pair."""
    try:
        items = news.fetch_calendar()
    except Exception as e:
        log.warning("Calendar fetch for sheet sync failed: %s", e)
        return

    ist = pytz.timezone(CFG.timezone)
    now = datetime.now(ist)
    # Look back the full week so past events retain their Actual values in the sheet
    window_start = now - timedelta(days=7)
    window_end = now + timedelta(days=7)
    relevant = [
        n for n in items
        if n.country in RELEVANT_COUNTRIES
        and n.impact in ("High", "Medium")
        and window_start <= n.date <= window_end
    ]
    rows = sheets_sync.build_news_rows(relevant)
    sheets_sync.sync_news(rows, now.isoformat())


def main() -> int:
    log.info("=== News watcher start ===")
    _sync_calendar_to_sheet()
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
