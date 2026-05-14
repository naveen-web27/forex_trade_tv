"""End-of-day report — runs ~11 PM IST.

1. Evaluate all OPEN trades against latest 15m candles
2. Compute today's P&L
3. Send Telegram summary + commit updated trades.csv
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime

import pandas as pd
import pytz

from src import data, telegram_notify, trade_log
from src.config import CFG, PAIRS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_eod")


def _today_pnl(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"opened": 0, "closed": 0, "wins": 0, "losses": 0,
                "r_total": 0.0, "usd_total": 0.0, "open_count": 0}
    today = datetime.now(pytz.timezone(CFG.timezone)).date()
    df["ts"] = pd.to_datetime(df["timestamp_ist"])
    today_df = df[df["ts"].dt.date == today]
    closed_today = today_df[today_df["status"].isin(["TP1_HIT", "TP2_HIT", "SL_HIT", "EXPIRED"])]
    if not closed_today.empty:
        closed_today = closed_today.copy()
        closed_today["result_r"]   = closed_today["result_r"].astype(float)
        closed_today["result_usd"] = closed_today["result_usd"].astype(float)
        wins   = (closed_today["result_r"] > 0).sum()
        losses = (closed_today["result_r"] <= 0).sum()
        return {
            "opened":   len(today_df),
            "closed":   len(closed_today),
            "wins":     int(wins),
            "losses":   int(losses),
            "r_total":  round(closed_today["result_r"].sum(), 2),
            "usd_total": round(closed_today["result_usd"].sum(), 2),
            "open_count": int((today_df["status"] == "OPEN").sum()),
            "rows": closed_today,
        }
    return {"opened": len(today_df), "closed": 0, "wins": 0, "losses": 0,
            "r_total": 0.0, "usd_total": 0.0,
            "open_count": int((today_df["status"] == "OPEN").sum())}


def _format_eod(s: dict, lifetime: dict) -> str:
    today = datetime.now(pytz.timezone(CFG.timezone)).strftime("%a %d %b %Y")
    pnl_emoji = "🟢" if s["r_total"] >= 0 else "🔴"
    lines = [
        f"📊 <b>END OF DAY REPORT — {today}</b>",
        "═" * 28,
        "",
        "<b>TODAY:</b>",
        f"  Signals fired: <b>{s['opened']}</b>",
        f"  Closed:        <b>{s['closed']}</b> ({s['wins']}W / {s['losses']}L)",
        f"  Still open:    <b>{s['open_count']}</b>",
        f"  {pnl_emoji} P&L:           <b>{s['r_total']:+.2f}R  /  ${s['usd_total']:+,.2f}</b>",
    ]
    if "rows" in s and not s["rows"].empty:
        lines += ["", "<b>Today's closed trades:</b>"]
        for _, r in s["rows"].iterrows():
            res_r = float(r["result_r"])
            icon = "✅" if res_r > 0 else "❌"
            lines.append(f"  {icon} {r['strategy']} {r['side']} {r['symbol']} "
                         f"→ {r['status']}  ({res_r:+.2f}R)")
    lines += [
        "",
        "<b>LIFETIME:</b>",
        f"  Total trades: {lifetime['total']}",
        f"  Win rate:     {lifetime['winrate']}%",
        f"  Total R:      {lifetime['total_r']:+.2f}",
        f"  Total $:      ${lifetime['total_usd']:+,.2f}",
        f"  Open now:     {lifetime['open']}",
        "",
        "<i>Trade log: data/trades.csv (committed to repo)</i>",
    ]
    return "\n".join(lines)


def main() -> int:
    log.info("=== EOD report start ===")

    # 1) Fetch fresh candles per pair, evaluate open trades
    market_data = {}
    for pair in PAIRS:
        if not pair.enabled:
            continue
        try:
            df = data.fetch_yf(pair.yf_symbol, interval=CFG.timeframe, days=CFG.history_days)
            market_data[pair.display] = df
            log.info("Fetched %s: %d candles", pair.display, len(df))
        except Exception as e:
            log.warning("Fetch %s failed: %s", pair.display, e)

    updated = trade_log.evaluate_open_trades(market_data)
    log.info("Evaluated open trades: %d updated", updated)

    # 2) Today's P&L
    df_all = trade_log.load_log()
    today = _today_pnl(df_all)
    lifetime = trade_log.stats_summary(df_all)

    # 3) Send
    msg = _format_eod(today, lifetime)
    ok = telegram_notify.send(msg)
    log.info("EOD report sent: %s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
