"""Signal scanner — multi-pair, every 15 min.

For each enabled pair × each strategy:
  1. Fetch OHLC
  2. Run strategy.check() on last closed bar
  3. If signal → compute lot size, send to Telegram, append to trade CSV
  4. Skip if red news within ±30 min

S6 (Virgin CPR) is handled separately from directional strategies:
  - Runs once per session, not per bar
  - Produces a consolidated multi-pair summary Telegram message
  - Has its own state file (vcpr_seen.json) to suppress repeats
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_vcpr")

# Path for VCPR dedup state (separate from directional-signal state)
VCPR_STATE_FILE = Path(CFG.state_file).parent / "vcpr_seen.json"

IST = timezone(timedelta(hours=5, minutes=30))





# ─────────────────────────────────────────────────────────────────────────────
# VCPR Telegram message formatter
# ─────────────────────────────────────────────────────────────────────────────

def _format_vcpr_message(all_reports) -> str:
    now_ist = datetime.now(IST)
    ts = now_ist.strftime("%d %b %Y %H:%M IST")

    header = "🌅 👻 <b>Virgin CPR Consolidated Alert</b>"

    lines = [
        header,
        f"🕐 {ts}",
        "════════════════════════════"
    ]

    total_count = 0

    for symbol, reports in all_reports.items():
        if not reports:
            continue

        total_count += len(reports)

        lines.append(
            f"\n🔹 <b>{symbol}</b> | "
            f"<b>VCPR Count:</b> {len(reports)}"
        )

        for report in reports:
            lines.append(
                f"   └─Date: {report[0]} | width: {report[3]:.1f}"
            )

    lines += [
        "",
        "════════════════════════════",
        f"📊 <b>Total Active VCPRs:</b> {total_count}",
        "",
        "📖 <b>Guide:</b>",
        "🔴 Wide CPR = strong magnet / bigger reaction",
        "🟢 Narrow CPR = breakout probability high",
        "⚡ Action = wait for reaction + confirmation candle"
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# VCPR scan — runs alongside directional strategies
# ─────────────────────────────────────────────────────────────────────────────



def safe_vcpr(symbol, exchange="FX", retries=5):
    for attempt in range(retries):
        try:
            result = td_vcpr_check(symbol, exchange=exchange)
            return result if result else []
        except Exception as e:
            print(f"[{symbol}] Attempt {attempt+1}/{retries} failed: {e}")
    return []
def main() -> int:


    all_reports = {
        "EURUSD": safe_vcpr("EURUSD"),
        "USDJPY": safe_vcpr("USDJPY"),
        "GBPUSD": safe_vcpr("GBPUSD"),
        "AUDUSD": safe_vcpr("AUDUSD"),
        "USDCHF": safe_vcpr("USDCHF"),
        "EURJPY": safe_vcpr("EURJPY"),
        "GBPJPY": safe_vcpr("GBPJPY"),
        "XAUUSD": safe_vcpr("XAUUSD"),
        "NZDCHF": safe_vcpr("NZDCHF"),
        "USDCAD": safe_vcpr("USDCAD"),
        "AUDNZD": safe_vcpr("AUDNZD"),
        "AUDCAD": safe_vcpr("AUDCAD"),

    }

    telegram_notify.send(_format_vcpr_message(all_reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())