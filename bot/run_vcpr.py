"""VCPR daily scan — runs twice per day.

Scans all pairs for Virgin CPR bands, then:
  1. Saves the active bands to vcpr_active.json  (read by run_vcpr_monitor.py)
  2. Sends a consolidated Telegram summary message

Schedule (cron example — run at 7:30 and 13:30 IST):
  30 2,8 * * 1-5  cd /path/to/bot && python run_vcpr.py
"""
from __future__ import annotations

import importlib
import logging
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src import data, news, telegram_notify, state, trade_log, position_size
from src.config import CFG, PAIRS
from src.formatters import signal_message

# ── VCPR imports ──────────────────────────────────────────────────────────────
from src.strategies.s6_virgin_cpr import check as vcpr_check, VCprReport
from src.strategies.s7_td_vcpr import check as td_vcpr_check
from src.strategies.s8_weekly_monthly_vcpr import check as wm_vcpr_check
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_vcpr")

# Path for VCPR dedup state (separate from directional-signal state)
VCPR_STATE_FILE = Path(CFG.state_file).parent / "vcpr_seen.json"

# Path where active VCPR bands are saved for the 15-min monitor to read
VCPR_ACTIVE_FILE = Path(CFG.state_file).parent / "vcpr_active.json"

IST = timezone(timedelta(hours=5, minutes=30))





# ─────────────────────────────────────────────────────────────────────────────
# VCPR Telegram message formatter
# ─────────────────────────────────────────────────────────────────────────────

def _format_vcpr_message(daily: dict, weekly: dict, monthly: dict) -> str:
    now_ist = datetime.now(IST)
    ts = now_ist.strftime("%d %b %Y %H:%M IST")

    lines = [
        "🌅 👻 <b>Virgin CPR — Daily · Weekly · Monthly</b>",
        f"🕐 {ts}",
        "════════════════════════════",
    ]

    all_symbols = sorted(set(list(daily) + list(weekly) + list(monthly)))
    d_total = w_total = m_total = 0

    for symbol in all_symbols:
        d = daily.get(symbol, [])
        w = weekly.get(symbol, [])
        m = monthly.get(symbol, [])
        if not d and not w and not m:
            continue

        d_total += len(d)
        w_total += len(w)
        m_total += len(m)

        lines.append(
            f"\n🔹 <b>{symbol}</b> "
            f"| D:{len(d)}  W:{len(w)}  M:{len(m)}"
        )
        for r in d:
            lines.append(f"   🟣 Daily  {r[0]} | w={r[3]:.5f}")
        for r in w:
            lines.append(f"   🔵 Weekly {r[0]} | w={r[3]:.5f}")
        for r in m:
            lines.append(f"   🟠 Monthly {r[0]} | w={r[3]:.5f}")

    lines += [
        "",
        "════════════════════════════",
        f"📊 Daily:{d_total}  Weekly:{w_total}  Monthly:{m_total}",
        "",
        "📖 <b>Guide:</b>",
        "🟣 Daily  = 3-5/week  | medium strength",
        "🔵 Weekly = 1-2/month | strong HTF magnet",
        "🟠 Monthly= 1-2/qtr   | institutional level ⭐",
        "⚡ Wait for reaction + confirmation candle",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# VCPR scan — runs alongside directional strategies
# ─────────────────────────────────────────────────────────────────────────────



PAIRS_LIST = [
    "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF",
    "EURJPY", "GBPJPY", "XAUUSD", "NZDCHF", "USDCAD",
    "AUDNZD", "AUDCAD",
]


def safe_vcpr_daily(symbol: str, exchange: str = "FX", retries: int = 5) -> list:
    for attempt in range(retries):
        try:
            result = td_vcpr_check(symbol, exchange=exchange)
            return result if result else []
        except Exception as e:
            log.warning("[%s] daily attempt %d/%d: %s", symbol, attempt + 1, retries, e)
    return []


def safe_vcpr_wm(symbol: str, exchange: str = "FX") -> dict:
    """Returns {"weekly": [...], "monthly": [...]} via S8 strategy (retries built-in)."""
    try:
        return wm_vcpr_check(symbol, exchange=exchange)
    except Exception as e:
        log.warning("[%s] weekly/monthly scan failed: %s", symbol, e)
        return {"weekly": [], "monthly": []}


def _save_vcpr_active(daily: dict, weekly: dict, monthly: dict) -> None:
    """Persist all three timeframe VCPR bands to vcpr_active.json."""
    def _to_list(reports: list) -> list:
        return [
            {"date": str(r[0])[:10], "bcpr": float(r[1]),
             "tcpr": float(r[2]),    "width": float(r[3])}
            for r in reports
        ]

    payload = {
        "scan_time": datetime.now(IST).isoformat(),
        "daily":   {s: _to_list(v) for s, v in daily.items()   if v},
        "weekly":  {s: _to_list(v) for s, v in weekly.items()  if v},
        "monthly": {s: _to_list(v) for s, v in monthly.items() if v},
    }
    VCPR_ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VCPR_ACTIVE_FILE, "w") as fh:
        json.dump(payload, fh, indent=2)
    log.info(
        "Saved daily=%d  weekly=%d  monthly=%d pairs to %s",
        len(payload["daily"]), len(payload["weekly"]), len(payload["monthly"]),
        VCPR_ACTIVE_FILE,
    )


def main() -> int:
    daily:   dict[str, list] = {}
    weekly:  dict[str, list] = {}
    monthly: dict[str, list] = {}

    for symbol in PAIRS_LIST:
        daily[symbol] = safe_vcpr_daily(symbol)
        wm = safe_vcpr_wm(symbol)
        weekly[symbol]  = wm["weekly"]
        monthly[symbol] = wm["monthly"]

    _save_vcpr_active(daily, weekly, monthly)
    telegram_notify.send(_format_vcpr_message(daily, weekly, monthly))
    return 0


if __name__ == "__main__":
    sys.exit(main())