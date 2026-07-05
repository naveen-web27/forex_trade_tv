"""15-minute VCPR proximity monitor.

Reads vcpr_active.json (written by run_vcpr.py) and checks whether the
current price of each pair is approaching any active Virgin CPR band.

Proximity rule
--------------
Expand each band by PROXIMITY_EXPANSION × band_width on both sides.
  proximity_low  = bcpr − (width × PROXIMITY_EXPANSION)
  proximity_high = tcpr + (width × PROXIMITY_EXPANSION)
If current_close falls inside that expanded zone → price is "close to VCPR".

De-duplication
--------------
  State file : bot/state/vcpr_proximity_seen.json
  Key format : "SYMBOL_YYYY-MM-DD"  (e.g. "EURUSD_2026-07-02")
  Value      : ISO timestamp of the last alert sent
  Re-alert   : only after ALERT_COOLDOWN_HOURS since last alert (default 4 h)
  This means the same VCPR can alert multiple times across a trading day if
  price keeps coming back, but won't spam every 15 min.

Schedule (cron — every 15 min, Mon–Fri):
  */15 * * * 1-5  cd /path/to/bot && python run_vcpr_monitor.py
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from tvDatafeed import TvDatafeed, Interval

from src import telegram_notify
from src.config import CFG

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_vcpr_monitor")

# ── paths ─────────────────────────────────────────────────────────────────────
_STATE_DIR          = Path(CFG.state_file).parent
VCPR_ACTIVE_FILE    = _STATE_DIR / "vcpr_active.json"
PROXIMITY_SEEN_FILE = _STATE_DIR / "vcpr_proximity_seen.json"

# ── tunables ──────────────────────────────────────────────────────────────────
PROXIMITY_EXPANSION  = 1.0   # expand band by 1× width on each side
EXCHANGE             = "FX"  # TradingView exchange used for all pairs

# Cooldown per timeframe — higher timeframe = longer wait before re-alerting
COOLDOWN_HOURS: dict[str, int] = {
    "daily":   4,    # same daily VCPR can re-alert after 4 h
    "weekly":  12,   # weekly VCPR re-alert after 12 h
    "monthly": 24,   # monthly VCPR re-alert after 24 h
}

# Emoji prefix per timeframe for easy identification in Telegram
TF_EMOJI: dict[str, str] = {
    "daily":   "🟣",
    "weekly":  "🔵",
    "monthly": "🟠",
}

# ── timezone ──────────────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

# ── shared TvDatafeed instance ────────────────────────────────────────────────
_tv = TvDatafeed()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            with open(path) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def _fetch_current_price(symbol: str, exchange: str = EXCHANGE, retries: int = 5) -> float | None:
    """Return the close price of the most recent completed 15-min candle."""
    for attempt in range(retries):
        try:
            df = _tv.get_hist(symbol=symbol, exchange=exchange,
                              interval=Interval.in_15_minutes, n_bars=3)
            if df is None or df.empty:
                raise ValueError("empty response")
            # Last row may be the still-forming candle; use second-to-last to be safe
            return float(df["close"].iloc[-2])
        except Exception as exc:
            log.warning("[%s] price fetch attempt %d/%d failed: %s", symbol, attempt + 1, retries, exc)
    return None


def _should_alert(seen: dict, key: str, cooldown_hours: int) -> bool:
    """Return True if no alert has been sent for this key within the cooldown window."""
    last_str = seen.get(key)
    if not last_str:
        return True
    try:
        last_dt = datetime.fromisoformat(last_str)
        elapsed = datetime.now(IST) - last_dt
        return elapsed >= timedelta(hours=cooldown_hours)
    except ValueError:
        return True


def _format_alert(symbol: str, price: float, triggered: list[dict], timeframe: str) -> str:
    """Build a Telegram HTML message for one pair/timeframe with proximity hits."""
    now_ist = datetime.now(IST).strftime("%d %b %Y %H:%M IST")
    emoji = TF_EMOJI.get(timeframe, "⚡")
    lines = [
        f"{emoji} <b>VCPR Proximity — {symbol} ({timeframe.upper()})</b>",
        f"🕐 {now_ist}",
        f"💹 <b>Current price:</b> {price:.5f}",
        "────────────────────────",
    ]
    for b in triggered:
        midpoint = (b["bcpr"] + b["tcpr"]) / 2
        dist = abs(price - midpoint)
        direction = "🔼 above" if price > midpoint else "🔽 below"
        lines.append(
            f"📅 <b>{b['date']}</b> | "
            f"Band [{b['bcpr']:.5f} – {b['tcpr']:.5f}]"
        )
        lines.append(f"   ↳ Price is {direction} midpoint by {dist:.5f}")
    lines += [
        "────────────────────────",
        "📖 Wait for reaction + confirmation candle before entry.",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main scan
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    # ── 1. Load active VCPR bands (all three timeframes) ─────────────────────
    active = _load_json(VCPR_ACTIVE_FILE)
    if not active:
        log.info("vcpr_active.json is empty or missing — run run_vcpr.py first.")
        return 0

    # Support both old format (pairs key) and new format (daily/weekly/monthly)
    if "pairs" in active and "daily" not in active:
        tf_data = {"daily": active["pairs"], "weekly": {}, "monthly": {}}
    else:
        tf_data = {
            "daily":   active.get("daily",   {}),
            "weekly":  active.get("weekly",  {}),
            "monthly": active.get("monthly", {}),
        }

    scan_time = active.get("scan_time", "unknown")
    log.info("Loaded VCPR data from scan at %s", scan_time)

    # ── 2. Load dedup state ──────────────────────────────────────────────────
    seen: dict[str, str] = _load_json(PROXIMITY_SEEN_FILE)
    updated = False

    # ── 3. Collect all symbols across timeframes ─────────────────────────────
    all_symbols = set()
    for bands_dict in tf_data.values():
        all_symbols.update(bands_dict.keys())

    # ── 4. Check each symbol × each timeframe ────────────────────────────────
    for symbol in sorted(all_symbols):
        price = _fetch_current_price(symbol)
        if price is None:
            log.warning("[%s] skipping — could not fetch current price", symbol)
            continue

        for timeframe, cooldown_hours in COOLDOWN_HOURS.items():
            bands = tf_data[timeframe].get(symbol, [])
            if not bands:
                continue

            triggered: list[dict] = []
            for b in bands:
                proximity_low  = b["bcpr"] - b["width"] * PROXIMITY_EXPANSION
                proximity_high = b["tcpr"] + b["width"] * PROXIMITY_EXPANSION

                if proximity_low <= price <= proximity_high:
                    key = f"{symbol}_{timeframe}_{b['date']}"
                    if _should_alert(seen, key, cooldown_hours):
                        triggered.append(b)
                        seen[key] = datetime.now(IST).isoformat()
                        updated = True
                    else:
                        log.debug("[%s/%s] %s already alerted recently", symbol, timeframe, b["date"])

            if triggered:
                msg = _format_alert(symbol, price, triggered, timeframe)
                telegram_notify.send(msg)
                log.info("[%s/%s] sent proximity alert for %d band(s)", symbol, timeframe, len(triggered))

        log.info("[%s] price=%.5f checked", symbol, price)

    # ── 5. Persist updated dedup state ───────────────────────────────────────
    if updated:
        _save_json(PROXIMITY_SEEN_FILE, seen)

    return 0


if __name__ == "__main__":
    sys.exit(main())
