"""Telegram /commands handler — polls getUpdates every 5 min and responds.

Supported commands (send in your group, bot must be admin):
    /status   — open trades, today's signals
    /today    — today's P&L
    /stats    — lifetime stats
    /levels   — current CPR, PDH/PDL for XAUUSD
    /help     — list commands

State: stores last processed update_id in bot/state/cmd_offset.json
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz
import requests

from src import data, trade_log, indicators as ind
from src.config import CFG, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.telegram_notify import send

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("commands")

OFFSET_FILE = Path("bot/state/cmd_offset.json")


def _load_offset() -> int:
    if OFFSET_FILE.exists():
        try:
            return int(json.loads(OFFSET_FILE.read_text()).get("offset", 0))
        except Exception:
            return 0
    return 0


def _save_offset(offset: int) -> None:
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(json.dumps({"offset": offset}))


def get_updates(offset: int) -> list:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    r = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=20)
    if r.status_code != 200:
        log.error("getUpdates failed: %s", r.text)
        return []
    return r.json().get("result", [])


# ───── Command implementations ─────

def cmd_help() -> str:
    return (
        "<b>🤖 Available commands:</b>\n"
        "/status   — current open trades + today\n"
        "/today    — today's P&amp;L summary\n"
        "/stats    — lifetime stats\n"
        "/levels   — XAUUSD CPR + PDH/PDL\n"
        "/help     — this message"
    )


def cmd_status() -> str:
    df = trade_log.load_log()
    if df.empty:
        return "📭 No trades logged yet."
    open_df = df[df["status"] == "OPEN"]
    today = datetime.now(pytz.timezone(CFG.timezone)).date()
    df["ts"] = pd.to_datetime(df["timestamp_ist"])
    today_df = df[df["ts"].dt.date == today]
    lines = [f"📋 <b>STATUS</b>\n",
             f"Today signals: <b>{len(today_df)}</b>",
             f"Open trades:   <b>{len(open_df)}</b>"]
    if not open_df.empty:
        lines.append("\n<b>Open positions:</b>")
        for _, r in open_df.tail(10).iterrows():
            lines.append(f"  • {r['strategy']} {r['side']} {r['symbol']} @ {r['entry']} "
                         f"(SL {r['sl']}, TP2 {r['tp2']})")
    return "\n".join(lines)


def cmd_today() -> str:
    df = trade_log.trades_today()
    if df.empty:
        return "📭 No signals today yet."
    closed = df[df["status"].isin(["TP1_HIT", "TP2_HIT", "SL_HIT", "EXPIRED"])].copy()
    open_n = (df["status"] == "OPEN").sum()
    if closed.empty:
        return f"📊 <b>TODAY</b>\n\nFired: {len(df)}\nClosed: 0\nOpen: {open_n}"
    closed["result_r"] = closed["result_r"].astype(float)
    closed["result_usd"] = closed["result_usd"].astype(float)
    wins = (closed["result_r"] > 0).sum()
    total_r = closed["result_r"].sum()
    total_usd = closed["result_usd"].sum()
    emoji = "🟢" if total_r >= 0 else "🔴"
    return (f"📊 <b>TODAY</b>\n"
            f"Fired:   {len(df)}\n"
            f"Closed:  {len(closed)} ({wins}W/{len(closed)-wins}L)\n"
            f"Open:    {open_n}\n"
            f"{emoji} P&amp;L:   <b>{total_r:+.2f}R  /  ${total_usd:+,.2f}</b>")


def cmd_stats() -> str:
    s = trade_log.stats_summary()
    if s["total"] == 0:
        return "📭 No closed trades yet."
    return (f"📈 <b>LIFETIME STATS</b>\n"
            f"Total trades: {s['total']}\n"
            f"Win rate:     {s['winrate']}%\n"
            f"Total R:      {s['total_r']:+.2f}\n"
            f"Total $:      ${s['total_usd']:+,.2f}\n"
            f"Open now:     {s['open']}")


def cmd_levels() -> str:
    try:
        daily = data.fetch_daily("GC=F", days=10)
        if len(daily) < 2:
            return "Insufficient data."
        p = daily.iloc[-2]
        pdh, pdl, pdc = float(p["high"]), float(p["low"]), float(p["close"])
        cur = float(daily.iloc[-1]["close"])
        cpr = ind.compute_cpr(pdh, pdl, pdc, cur)
        return (f"🎯 <b>XAUUSD LEVELS</b>\n"
                f"Last:   <code>{cur:,.2f}</code>\n"
                f"PDH:    <code>{pdh:,.2f}</code>\n"
                f"PDL:    <code>{pdl:,.2f}</code>\n"
                f"Pivot:  <code>{cpr.pivot:,.2f}</code>\n"
                f"CPR TC: <code>{cpr.tc:,.2f}</code>\n"
                f"CPR BC: <code>{cpr.bc:,.2f}</code>\n"
                f"Width:  {cpr.width_pct:.2f}%")
    except Exception as e:
        return f"⚠️ Error fetching levels: {e}"


COMMANDS = {
    "/help":   cmd_help,
    "/status": cmd_status,
    "/today":  cmd_today,
    "/stats":  cmd_stats,
    "/levels": cmd_levels,
}


def main() -> int:
    log.info("=== Command handler start ===")
    offset = _load_offset()
    updates = get_updates(offset)
    if not updates:
        log.info("No new messages.")
        return 0

    max_id = offset
    for upd in updates:
        max_id = max(max_id, upd["update_id"] + 1)
        msg = upd.get("message") or upd.get("channel_post")
        if not msg:
            continue
        chat = msg.get("chat", {})
        # Only respond in configured chat
        if str(chat.get("id")) != str(TELEGRAM_CHAT_ID):
            continue
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            continue
        # Strip @botname
        cmd = text.split()[0].split("@")[0].lower()
        handler = COMMANDS.get(cmd)
        if not handler:
            continue
        log.info("Handling %s", cmd)
        try:
            reply = handler()
        except Exception as e:
            reply = f"⚠️ Error: {e}"
        send(reply)

    _save_offset(max_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
