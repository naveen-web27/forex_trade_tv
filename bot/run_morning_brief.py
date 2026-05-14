"""Daily morning brief — sent at 11:30 AM IST.

Pulls: today's red news, DXY/US10Y/Gold snapshot, key XAUUSD daily levels,
and computes a simple bullish/bearish bias.
"""
from __future__ import annotations

import logging
import sys

from src import data, news, telegram_notify
from src.config import CFG
from src.formatters import morning_brief
from src import indicators as ind

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("morning_brief")


def compute_bias(macro: dict) -> str:
    """Very simple bias: DXY direction + yields direction → gold bias."""
    dxy = macro.get("DXY (Dollar Index)", {}).get("change_pct", 0)
    y10 = macro.get("US 10Y Yield", {}).get("change_pct", 0)
    score = -dxy - y10  # positive score = bullish gold
    if score > 0.3:
        return "🟢 BULLISH gold (DXY/yields weak)"
    if score < -0.3:
        return "🔴 BEARISH gold (DXY/yields strong)"
    return "⚪ NEUTRAL (mixed signals — be selective)"


def main() -> int:
    log.info("=== Morning brief start ===")

    try:
        red = news.todays_red_news()
        log.info("Red news today: %d", len(red))
    except Exception as e:
        log.warning("News failed: %s", e)
        red = []

    macro = {}
    try:
        macro = data.fetch_macro_snapshot()
        log.info("Macro snapshot: %d symbols", len(macro))
    except Exception as e:
        log.warning("Macro failed: %s", e)

    levels = {}
    try:
        daily = data.fetch_daily(days=10)
        if len(daily) >= 2:
            p = daily.iloc[-2]
            pdh, pdl, pdc = float(p["high"]), float(p["low"]), float(p["close"])
            cur = float(daily.iloc[-1]["close"]) if len(daily) >= 1 else pdc
            cpr = ind.compute_cpr(pdh, pdl, pdc, cur)
            levels = {
                "PDH":       pdh,
                "PDL":       pdl,
                "PDC":       pdc,
                "Pivot":     cpr.pivot,
                "CPR TC":    cpr.tc,
                "CPR BC":    cpr.bc,
            }
    except Exception as e:
        log.warning("Levels failed: %s", e)

    bias = compute_bias(macro)
    text = morning_brief(red, macro, levels, bias)
    ok = telegram_notify.send(text)
    log.info("Morning brief sent: %s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
