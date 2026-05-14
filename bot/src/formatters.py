"""HTML formatters for Telegram messages."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .strategies import Signal
from .news import NewsItem
from .quotes import quote_of_the_day


def _fmt_price(p: float) -> str:
    return f"{p:,.2f}"


def signal_message(s: Signal, acct: float, risk_pct: float,
                   lot_size: float = 0.0, risk_usd: float = 0.0) -> str:
    sl_dist = abs(s.entry - s.sl)
    side_emoji = "🟢" if s.side == "LONG" else "🔴"
    arrow = "↑" if s.side == "LONG" else "↓"
    lot_line = (f"📦 <b>Lot size</b>: <code>{lot_size:.2f}</code> "
                f"(risk ${risk_usd:.0f} = {risk_pct}% of ${acct:,.0f})\n"
                if lot_size > 0 else
                f"💰 Risk @ {risk_pct}% = ${acct * risk_pct/100:,.0f}\n")
    return (
        f"{side_emoji} <b>{s.strategy} {s.side}</b>  {s.symbol} {arrow}\n"
        f"<i>{s.name}</i>\n"
        f"────────────────────\n"
        f"<b>Entry</b>: <code>{_fmt_price(s.entry)}</code>\n"
        f"<b>SL   </b>: <code>{_fmt_price(s.sl)}</code>   "
        f"(Δ {_fmt_price(sl_dist)})\n"
        f"<b>TP1  </b>: <code>{_fmt_price(s.tp1)}</code>   ({s.rr1:.1f}R)\n"
        f"<b>TP2  </b>: <code>{_fmt_price(s.tp2)}</code>   ({s.rr2:.1f}R)\n"
        f"────────────────────\n"
        f"💡 {s.reason}\n"
        f"{lot_line}"
        f"🕒 {s.bar_time.strftime('%a %d %b %H:%M IST')}\n"
        f"\n⚠️ <b>Verify on chart. Don't chase. Use EXACT lot above.</b>"
    )


def morning_brief(red_today: list[NewsItem],
                  macro: dict,
                  daily_levels: dict,
                  bias: str) -> str:
    today = datetime.now().strftime("%a %d %b %Y")
    lines = [
        f"🌅 <b>GOOD MORNING — {today}</b>",
        "═" * 28,
        "",
        "📰 <b>RED NEWS TODAY (USD/EUR/GBP):</b>",
    ]
    if not red_today:
        lines.append("  ✅ No red-impact news. Free to trade normally.")
    else:
        for n in red_today:
            lines.append(f"  🔴 {n.date.strftime('%H:%M IST')} | {n.country} | {n.title}")
        lines.append("  ⚠️ Avoid trades 30 min around each.")

    lines += ["", "📊 <b>MACRO SNAPSHOT:</b>"]
    for name, info in macro.items():
        sign = "📈" if info["change_pct"] >= 0 else "📉"
        lines.append(f"  {sign} {name}: <code>{info['price']:,.2f}</code> "
                     f"({info['change_pct']:+.2f}%)")

    if daily_levels:
        lines += ["", "🎯 <b>KEY LEVELS XAUUSD:</b>"]
        for k, v in daily_levels.items():
            lines.append(f"  {k}: <code>{v:,.2f}</code>")

    lines += ["", f"🧭 <b>BIAS</b>: {bias}", "",
              "─" * 28,
              quote_of_the_day(),
              "",
              "<i>🎯 Stick to the plan. Risk ≤ 0.3%. Max 2 trades/day. Stop after 2 losses.</i>"]
    return "\n".join(lines)


def news_warning(items: list[NewsItem]) -> str:
    lines = ["⚠️ <b>UPCOMING RED NEWS</b>", "─" * 26]
    for n in items:
        mins = int((n.date - datetime.now(n.date.tzinfo)).total_seconds() / 60)
        lines.append(f"🔴 {n.title}")
        lines.append(f"   {n.country} | {n.date.strftime('%H:%M IST')} "
                     f"(<b>in {mins} min</b>)")
        if n.forecast or n.previous:
            lines.append(f"   Forecast: {n.forecast or '—'}  |  Prev: {n.previous or '—'}")
        lines.append("")
    lines.append("⛔ <b>Close positions 15-30 min before. Spread will widen.</b>")
    return "\n".join(lines)
