"""Fetch macro / economic-calendar news from ForexFactory weekly XML.

Free, no API key. URL: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import pytz
import requests
from lxml import etree

from .config import CFG

log = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    country: str
    date: datetime  # tz-aware in IST
    impact: str     # "High" / "Medium" / "Low" / "Holiday"
    forecast: str
    previous: str
    actual: str

    def is_red(self) -> bool:
        return self.impact.lower() == "high"

    def emoji(self) -> str:
        return {"High": "🔴", "Medium": "🟠", "Low": "🟡", "Holiday": "🏖"}.get(self.impact, "⚪")


def fetch_calendar() -> List[NewsItem]:
    """Return all events this week (in IST)."""
    try:
        r = requests.get(CFG.ff_calendar_url, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        log.error("Calendar fetch failed: %s", e)
        return []

    tree = etree.fromstring(r.content)
    ist = pytz.timezone(CFG.timezone)
    items: List[NewsItem] = []

    for ev in tree.findall(".//event"):
        def g(tag: str) -> str:
            el = ev.find(tag)
            return (el.text or "").strip() if el is not None else ""
        date_s = g("date")  # e.g. "05-15-2026"
        time_s = g("time")  # e.g. "8:30am" OR "All Day" OR "Tentative"
        try:
            # ForexFactory uses US/Eastern timezone in XML
            if not time_s or time_s.lower() in ("all day", "tentative"):
                dt = datetime.strptime(date_s, "%m-%d-%Y")
                dt_us = pytz.timezone("US/Eastern").localize(dt.replace(hour=0, minute=0))
            else:
                dt_str = f"{date_s} {time_s}"
                dt = datetime.strptime(dt_str, "%m-%d-%Y %I:%M%p")
                dt_us = pytz.timezone("US/Eastern").localize(dt)
            dt_ist = dt_us.astimezone(ist)
        except Exception:
            continue

        items.append(NewsItem(
            title=g("title"),
            country=g("country"),
            date=dt_ist,
            impact=g("impact") or "Low",
            forecast=g("forecast"),
            previous=g("previous"),
            actual=g("actual"),
        ))
    return items


def todays_red_news(now: datetime | None = None) -> List[NewsItem]:
    items = fetch_calendar()
    ist = pytz.timezone(CFG.timezone)
    now = now or datetime.now(ist)
    today = now.date()
    return [x for x in items
            if x.is_red() and x.date.date() == today and x.country in ("USD", "EUR", "GBP")]


def upcoming_red_news(within_minutes: int = 90) -> List[NewsItem]:
    items = fetch_calendar()
    ist = pytz.timezone(CFG.timezone)
    now = datetime.now(ist)
    horizon = now + timedelta(minutes=within_minutes)
    return [x for x in items
            if x.is_red() and now <= x.date <= horizon and x.country in ("USD", "EUR", "GBP")]


def red_news_active(buffer_minutes: int = 30) -> bool:
    """Return True if a red-impact event is within ±buffer_minutes of now.
    Used by signal scanner to skip trades around news.
    """
    ist = pytz.timezone(CFG.timezone)
    now = datetime.now(ist)
    items = fetch_calendar()
    for x in items:
        if x.is_red() and x.country in ("USD", "EUR", "GBP"):
            delta = abs((x.date - now).total_seconds()) / 60
            if delta <= buffer_minutes:
                return True
    return False
