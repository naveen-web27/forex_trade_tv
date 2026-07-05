"""15-minute VCPR proximity monitor.

Reads vcpr_active.json (written by run_vcpr.py) and checks whether the
current price of each pair is approaching any active Virgin CPR band.

Proximity rule
--------------
Alert only when the price is between PROXIMITY_PIPS_MIN and PROXIMITY_PIPS_MAX
pips away from the nearest band edge (bcpr or tcpr).
  • Price approaching from below  → distance = bcpr - price
  • Price approaching from above  → distance = price - tcpr
  • Price inside the band         → skipped (distance = 0)
Pip sizes: 0.01 for JPY pairs, 0.10 for XAU, 0.0001 for all others.

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
PROXIMITY_PIPS_MIN = 5    # don't alert if price is inside / touching band
PROXIMITY_PIPS_MAX = 20   # don't alert if price is farther than this from band
EXCHANGE           = "FX" # TradingView exchange used for all pairs

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

def _pip_size(symbol: str) -> float:
    """Return the pip/point size for pip-distance calculations."""
    sym = symbol.upper()
    if "JPY" in sym:
        return 0.01
    if "XAU" in sym:
        return 0.10
    return 0.0001


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


def _format_consolidated_alert(hits: list[dict]) -> str:
    """Build a single consolidated Telegram HTML message for all proximity hits."""
    from collections import defaultdict

    now_ist = datetime.now(IST).strftime("%d %b %Y %H:%M IST")
    lines = [
        "⚡ <b>VCPR Proximity Alert</b>",
        f"🕐 {now_ist}",
        "════════════════════════════",
    ]

    # Group hits by symbol (preserve sorted order)
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for hit in hits:
        by_symbol[hit["symbol"]].append(hit)

    for symbol, sym_hits in sorted(by_symbol.items()):
        price = sym_hits[0]["price"]
        lines.append(f"\n🔹 <b>{symbol}</b>  💹 Current: <b>{price:.5f}</b>")
        for h in sym_hits:
            b   = h["band"]
            tf  = h["timeframe"]
            emoji = TF_EMOJI.get(tf, "⚡")
            dist_pips = h["dist_pips"]
            dist_raw  = h["dist_raw"]
            if price < b["bcpr"]:
                direction = "🔼 approaching from below"
            else:
                direction = "🔽 approaching from above"
            lines.append(
                f"   {emoji} {tf.capitalize()} <b>{b['date']}</b>  "
                f"[{b['bcpr']:.5f} – {b['tcpr']:.5f}]"
            )
            lines.append(
                f"      ↳ {direction} | "
                f"Δ <b>{dist_pips:.1f} pips</b>  ({dist_raw:.5f})"
            )

    total_pairs = len(by_symbol)
    total_bands = len(hits)
    lines += [
        "",
        "════════════════════════════",
        f"📊 <b>{total_bands}</b> band(s) across <b>{total_pairs}</b> pair(s)",
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

    # ── 4. Check each symbol × each timeframe, collect all hits ──────────────
    all_hits: list[dict] = []

    for symbol in sorted(all_symbols):
        price = _fetch_current_price(symbol)
        if price is None:
            log.warning("[%s] skipping — could not fetch current price", symbol)
            continue

        pip = _pip_size(symbol)

        for timeframe, cooldown_hours in COOLDOWN_HOURS.items():
            bands = tf_data[timeframe].get(symbol, [])
            if not bands:
                continue

            for b in bands:
                # Distance from current price to the nearest band edge
                if price < b["bcpr"]:
                    dist_raw = b["bcpr"] - price   # approaching from below
                elif price > b["tcpr"]:
                    dist_raw = price - b["tcpr"]   # approaching from above
                else:
                    dist_raw = 0.0                 # inside the band — skip

                dist_pips = dist_raw / pip

                if not (PROXIMITY_PIPS_MIN <= dist_pips <= PROXIMITY_PIPS_MAX):
                    log.debug(
                        "[%s/%s] %s dist=%.1f pips — outside window [%d-%d]",
                        symbol, timeframe, b["date"],
                        dist_pips, PROXIMITY_PIPS_MIN, PROXIMITY_PIPS_MAX,
                    )
                    continue

                key = f"{symbol}_{timeframe}_{b['date']}"
                if _should_alert(seen, key, cooldown_hours):
                    all_hits.append({
                        "symbol":    symbol,
                        "price":     price,
                        "timeframe": timeframe,
                        "band":      b,
                        "dist_raw":  dist_raw,
                        "dist_pips": dist_pips,
                    })
                    seen[key] = datetime.now(IST).isoformat()
                    updated = True
                else:
                    log.debug("[%s/%s] %s already alerted recently", symbol, timeframe, b["date"])

        log.info("[%s] price=%.5f checked", symbol, price)

    # ── 5. Send ONE consolidated alert if there are any hits ─────────────────
    if all_hits:
        msg = _format_consolidated_alert(all_hits)
        telegram_notify.send(msg)
        log.info(
            "Sent consolidated alert: %d band(s) across %d pair(s)",
            len(all_hits),
            len({h["symbol"] for h in all_hits}),
        )
    else:
        log.info("No pairs within %d–%d pip window — no alert sent.",
                 PROXIMITY_PIPS_MIN, PROXIMITY_PIPS_MAX)

    # ── 6. Persist updated dedup state ───────────────────────────────────────
    if updated:
        _save_json(PROXIMITY_SEEN_FILE, seen)

    return 0


if __name__ == "__main__":
    sys.exit(main())
