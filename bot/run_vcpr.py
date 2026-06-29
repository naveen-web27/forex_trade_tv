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
log = logging.getLogger("run_signals")

# Path for VCPR dedup state (separate from directional-signal state)
VCPR_STATE_FILE = Path(CFG.state_file).parent / "vcpr_seen.json"

IST = timezone(timedelta(hours=5, minutes=30))


# ─────────────────────────────────────────────────────────────────────────────
# VCPR state helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_vcpr_state() -> dict:
    if VCPR_STATE_FILE.exists():
        try:
            return json.loads(VCPR_STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_vcpr_state(state_dict: dict):
    VCPR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VCPR_STATE_FILE.write_text(json.dumps(state_dict, indent=2))


def _vcpr_already_alerted(state_dict: dict, symbol: str, date: str) -> bool:
    return state_dict.get(symbol, {}).get(date, False)


def _vcpr_mark_alerted(state_dict: dict, symbol: str, date: str):
    if symbol not in state_dict:
        state_dict[symbol] = {}
    state_dict[symbol][date] = True
    # Prune entries older than 35 days to keep the file lean
    cutoff = (datetime.now(IST) - timedelta(days=35)).strftime("%Y-%m-%d")
    state_dict[symbol] = {
        d: v for d, v in state_dict[symbol].items() if d >= cutoff
    }


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
                f"   └─ {report}"
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

def run_vcpr_scan(pair_data_map: dict) -> int:
    """
    Scan all pairs for Virgin CPRs.
    Sends ONE consolidated Telegram message for all NEW virgin CPRs found.
    Also sends a full morning summary at 09:00–09:14 IST regardless of newness.

    Args:
        pair_data_map: {pair.display: (df_15m, df_daily)} — already fetched data

    Returns:
        int: number of new virgin CPR bands alerted across all pairs
    """
    log.info("=== Virgin CPR scan ===")
    vcpr_state = _load_vcpr_state()
    now_ist = datetime.now(IST)
    is_morning = (now_ist.hour == 9 and now_ist.minute < 15)

    all_reports: list[VCprReport] = []
    new_reports: list[VCprReport] = []   # only reports with NEW (un-alerted) bands

    for pair in PAIRS:
        if not pair.enabled:
            continue
        if pair.display not in pair_data_map:
            continue

        df, daily = pair_data_map[pair.display]
        try:
            report = vcpr_check(df, daily, pair.display)
            if report is None:
                continue

            all_reports.append(report)

            # Filter to only bands we haven't sent before
            new_bands = [
                b for b in report.bands
                if not _vcpr_already_alerted(vcpr_state, pair.display, b.date)
            ]
            if new_bands:
                from src.strategies.s6_virgin_cpr import VCprReport as R
                new_rpt = R(symbol=pair.display, bands=new_bands)
                new_reports.append(new_rpt)
                for b in new_bands:
                    _vcpr_mark_alerted(vcpr_state, pair.display, b.date)

        except Exception as e:
            log.exception("[%s] VCPR scan error: %s", pair.display, e)

    alerted = 0

    # Morning summary (09:00–09:14 IST) — send ALL current VCPRs
    if is_morning:
        msg = _format_vcpr_message(all_reports, is_morning=True)
        if telegram_notify.send(msg):
            log.info("📊 Morning VCPR summary sent.")
        else:
            log.error("Morning VCPR summary Telegram send failed.")

    # Alert for NEW virgin CPRs found this run (any time of day)
    elif new_reports:
        msg = _format_vcpr_message(new_reports, is_morning=False)
        if telegram_notify.send(msg):
            alerted = sum(len(r.bands) for r in new_reports)
            log.info("📬 VCPR alert sent: %d new band(s) across %d pair(s).",
                     alerted, len(new_reports))
        else:
            log.error("VCPR alert Telegram send failed.")

    else:
        log.info("VCPR: no new virgin CPRs this run.")

    _save_vcpr_state(vcpr_state)
    return alerted


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def fetch_for_pair(pair) -> tuple:
    df = data.fetch_yf(pair.yf_symbol, interval=CFG.timeframe, days=CFG.history_days)
    daily = data.fetch_daily(pair.yf_symbol, days=40)   # 40 days → covers VCPR lookback
    return df, daily

import time

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
    }

    telegram_notify.send(_format_vcpr_message(all_reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())