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
from tvDatafeed import TvDatafeed, Interval

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

_tv = TvDatafeed()


# ─────────────────────────────────────────────────────────────────────────────
# Price / pip helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pip_size(symbol: str) -> float:
    sym = symbol.upper()
    if "JPY" in sym:
        return 0.01
    if "XAU" in sym:
        return 0.10
    return 0.0001


def _fetch_current_prices(symbols: list[str], exchange: str = "FX",
                          retries: int = 5) -> dict[str, float]:
    """Return {symbol: latest_close} for every symbol we can fetch."""
    prices: dict[str, float] = {}
    for symbol in symbols:
        for attempt in range(retries):
            try:
                df = _tv.get_hist(symbol=symbol, exchange=exchange,
                                  interval=Interval.in_15_minutes, n_bars=3)
                if df is None or df.empty:
                    raise ValueError("empty response")
                prices[symbol] = float(df["close"].iloc[-2])
                break
            except Exception as e:
                log.warning("[%s] price fetch attempt %d/%d: %s",
                            symbol, attempt + 1, retries, e)
    return prices


def _band_pip_distance(price: float, bcpr: float, tcpr: float,
                       pip: float) -> tuple[float, float, str]:
    """Return (dist_raw, dist_pips, direction_label) for a band."""
    if price < bcpr:
        dist_raw = bcpr - price
        direction = "🔼 below band"
    elif price > tcpr:
        dist_raw = price - tcpr
        direction = "🔽 above band"
    else:
        dist_raw = 0.0
        direction = "↔ inside band"
    return dist_raw, dist_raw / pip, direction


# ─────────────────────────────────────────────────────────────────────────────
# VCPR Telegram message formatter
# ─────────────────────────────────────────────────────────────────────────────

def _format_vcpr_message(daily: dict, weekly: dict, monthly: dict,
                         prices: dict[str, float]) -> str:
    ts = datetime.now(IST).strftime("%d %b %H:%M IST")

    lines = [
        f"🌅👻 <b>Virgin CPR</b> · {ts}",
        "────────────────────",
    ]

    all_symbols = sorted(set(list(daily) + list(weekly) + list(monthly)))
    d_total = w_total = m_total = 0

    for symbol in all_symbols:
        price = prices.get(symbol)
        pip   = _pip_size(symbol)

        d = daily.get(symbol, [])
        w = weekly.get(symbol, [])
        m = monthly.get(symbol, [])

        if not d and not w and not m:
            continue

        d_total += len(d)
        w_total += len(w)
        m_total += len(m)

        price_str = f" {price:.5f}" if price is not None else ""
        lines.append(f"🔹<b>{symbol}</b>{price_str}")

        for r in d:
            dp = f" Δ<b>{_band_pip_distance(price, r[1], r[2], pip)[1]:.0f}p</b>" if price else ""
            lines.append(f"  🟣{_short_date(r[0])} {r[1]:.5f}–{r[2]:.5f}{dp}")
        for r in w:
            dp = f" Δ<b>{_band_pip_distance(price, r[1], r[2], pip)[1]:.0f}p</b>" if price else ""
            lines.append(f"  🔵{_short_date(r[0])} {r[1]:.5f}–{r[2]:.5f}{dp}")
        for r in m:
            dp = f" Δ<b>{_band_pip_distance(price, r[1], r[2], pip)[1]:.0f}p</b>" if price else ""
            lines.append(f"  🟠{_short_date(r[0])} {r[1]:.5f}–{r[2]:.5f}{dp}")

    if d_total + w_total + m_total == 0:
        return f"🌅👻 <b>Virgin CPR</b> · {ts}\nNo active VCPR bands found."

    lines += [
        "────────────────────",
        f"📊 D:{d_total} W:{w_total} M:{m_total}  ⚡confirm before entry",
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

    prices = _fetch_current_prices(PAIRS_LIST)
    telegram_notify.send(_format_vcpr_message(daily, weekly, monthly, prices))
    return 0


if __name__ == "__main__":
    sys.exit(main())
