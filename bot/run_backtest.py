"""Weekly backtest report — replays last 30d of M15 data per pair+strategy,
simulates trades and produces a markdown report committed to data/backtest_report.md
+ Telegram summary."""
from __future__ import annotations

import importlib
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytz

from src import data, telegram_notify
from src.config import CFG, PAIRS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backtest")


def simulate_strategy(strat_name: str, df_intraday: pd.DataFrame,
                      df_daily: pd.DataFrame, symbol: str) -> list[dict]:
    """Walk forward 1 bar at a time, calling strategy.check() like live.
    Then track each emitted signal forward to SL/TP2."""
    mod = importlib.import_module(f"src.strategies.{strat_name}")
    results = []
    seen_keys = set()

    # We need at least 220 bars of history before strategies become valid
    start = 220
    for i in range(start, len(df_intraday)):
        window = df_intraday.iloc[: i + 1]
        # Daily candles up to current intraday bar's date
        current_date = window.index[-1].date()
        daily_window = df_daily[df_daily.index.date <= current_date]
        if len(daily_window) < 3:
            continue
        try:
            sig = mod.check(window, daily_window, symbol)
        except Exception:
            continue
        if sig is None:
            continue
        key = sig.dedupe_key()
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # Simulate forward
        entry, sl, tp1, tp2 = sig.entry, sig.sl, sig.tp1, sig.tp2
        risk = abs(entry - sl)
        future = df_intraday.iloc[i + 1: i + 1 + 96]  # next 24h of M15
        outcome = "EXPIRED"
        result_r = 0.0
        for _, c in future.iterrows():
            hi, lo = float(c["high"]), float(c["low"])
            if sig.side == "LONG":
                if lo <= sl:
                    outcome = "SL"; result_r = -1.0; break
                if hi >= tp2:
                    outcome = "TP2"; result_r = (tp2 - entry) / risk; break
            else:
                if hi >= sl:
                    outcome = "SL"; result_r = -1.0; break
                if lo <= tp2:
                    outcome = "TP2"; result_r = (entry - tp2) / risk; break
        if outcome == "EXPIRED" and not future.empty:
            last_c = float(future.iloc[-1]["close"])
            result_r = ((last_c - entry) if sig.side == "LONG" else (entry - last_c)) / risk

        results.append({
            "strategy": sig.strategy, "symbol": symbol, "side": sig.side,
            "entry": entry, "sl": sl, "tp2": tp2,
            "time": sig.bar_time, "outcome": outcome, "result_r": result_r,
        })
    return results


def main() -> int:
    log.info("=== Weekly backtest start ===")
    all_results: list[dict] = []

    for pair in PAIRS:
        if not pair.enabled:
            continue
        try:
            df = data.fetch_yf(pair.yf_symbol, interval=CFG.timeframe, days=CFG.history_days)
            daily = data.fetch_daily(pair.yf_symbol, days=60)
            log.info("[%s] %d intraday, %d daily", pair.display, len(df), len(daily))
            if len(df) < 250:
                continue
        except Exception as e:
            log.warning("[%s] data failed: %s", pair.display, e)
            continue

        for strat_name in CFG.enable_strategies:
            try:
                r = simulate_strategy(strat_name, df, daily, pair.display)
                log.info("[%s/%s] %d signals", pair.display, strat_name, len(r))
                all_results.extend(r)
            except Exception as e:
                log.exception("[%s/%s] sim failed: %s", pair.display, strat_name, e)

    # Build report
    if not all_results:
        telegram_notify.send("📊 <b>Weekly Backtest</b>\n\nNo signals in last 30 days. Strategies very selective.")
        return 0

    df_r = pd.DataFrame(all_results)
    df_r.to_csv("data/backtest_signals.csv", index=False)

    # Per-strategy / per-symbol summary
    grouped = df_r.groupby(["symbol", "strategy"]).agg(
        trades=("result_r", "count"),
        wins=("result_r", lambda x: (x > 0).sum()),
        winrate=("result_r", lambda x: round((x > 0).mean() * 100, 1)),
        total_r=("result_r", lambda x: round(x.sum(), 2)),
        avg_r=("result_r", lambda x: round(x.mean(), 2)),
    ).reset_index()

    # Markdown
    md_lines = [
        f"# 📊 Backtest Report — last {CFG.history_days} days",
        f"_Generated: {datetime.now(pytz.timezone(CFG.timezone)).strftime('%Y-%m-%d %H:%M IST')}_",
        "",
        f"Total signals: **{len(df_r)}**",
        "",
        "## Per Strategy × Pair",
        "",
        grouped.to_markdown(index=False),
        "",
        "## Raw signals: see `data/backtest_signals.csv`",
    ]
    Path(CFG.bt_report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(CFG.bt_report_path).write_text("\n".join(md_lines))

    # Telegram top summary
    overall_winrate = round((df_r["result_r"] > 0).mean() * 100, 1)
    overall_r = round(df_r["result_r"].sum(), 2)
    msg = [
        f"📊 <b>WEEKLY BACKTEST</b> (last {CFG.history_days}d)",
        "═" * 26,
        f"Total signals: <b>{len(df_r)}</b>",
        f"Win rate:      <b>{overall_winrate}%</b>",
        f"Total R:       <b>{overall_r:+.2f}</b>",
        "",
        "<b>Top performers:</b>",
    ]
    top = grouped.sort_values("total_r", ascending=False).head(5)
    for _, row in top.iterrows():
        msg.append(f"  • {row['symbol']} {row['strategy']}: "
                   f"{int(row['trades'])} trades, {row['winrate']}% win, "
                   f"{row['total_r']:+.2f}R")
    msg += [
        "",
        "<b>Worst performers:</b>",
    ]
    bot = grouped.sort_values("total_r").head(3)
    for _, row in bot.iterrows():
        msg.append(f"  • {row['symbol']} {row['strategy']}: "
                   f"{int(row['trades'])} trades, {row['winrate']}% win, "
                   f"{row['total_r']:+.2f}R")
    msg.append("\n<i>Full report: data/backtest_report.md</i>")

    telegram_notify.send("\n".join(msg))
    log.info("=== Backtest done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
