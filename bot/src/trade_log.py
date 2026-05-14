"""Trade log: persist every signal to data/trades.csv and evaluate outcomes.

Schema (one row per signal):
    id,timestamp_ist,strategy,strategy_name,symbol,side,
    entry,sl,tp1,tp2,risk_dist,rr1,rr2,reason,
    lot_size,risk_usd,
    status,         # OPEN / TP1_HIT / TP2_HIT / SL_HIT / EXPIRED
    exit_price,exit_time_ist,result_r,result_usd,
    closed_at_ist

Two functions:
    append_signal(...)   — call when a new signal fires
    evaluate_open(df_by_symbol)  — for all OPEN trades, check if SL/TP1/TP2 hit
"""
from __future__ import annotations

import csv
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pytz

from .config import CFG
from .strategies import Signal

log = logging.getLogger(__name__)

CSV_PATH = Path(CFG.trade_log_csv)

HEADERS = [
    "id", "timestamp_ist", "strategy", "strategy_name", "symbol", "side",
    "entry", "sl", "tp1", "tp2", "risk_dist", "rr1", "rr2", "reason",
    "lot_size", "risk_usd",
    "status", "exit_price", "exit_time_ist", "result_r", "result_usd",
    "closed_at_ist",
]


def _ensure_file() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            csv.writer(f).writerow(HEADERS)


def append_signal(sig: Signal, lot_size: float, risk_usd: float) -> str:
    """Append a new signal as OPEN; return its id."""
    _ensure_file()
    sid = uuid.uuid4().hex[:10]
    risk_dist = abs(sig.entry - sig.sl)
    row = [
        sid, sig.bar_time.isoformat(), sig.strategy, sig.name, sig.symbol, sig.side,
        f"{sig.entry:.5f}", f"{sig.sl:.5f}", f"{sig.tp1:.5f}", f"{sig.tp2:.5f}",
        f"{risk_dist:.5f}", f"{sig.rr1:.2f}", f"{sig.rr2:.2f}", sig.reason,
        f"{lot_size:.4f}", f"{risk_usd:.2f}",
        "OPEN", "", "", "", "",
        "",
    ]
    with CSV_PATH.open("a", newline="") as f:
        csv.writer(f).writerow(row)
    return sid


def load_log() -> pd.DataFrame:
    _ensure_file()
    return pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)


def save_log(df: pd.DataFrame) -> None:
    df.to_csv(CSV_PATH, index=False)


def evaluate_open_trades(market_data: Dict[str, pd.DataFrame]) -> int:
    """For each OPEN trade, check candles AFTER its entry; if SL or TP2 hit
    (in chronological order), update its row. Returns count updated."""
    df = load_log()
    if df.empty:
        return 0
    updated = 0
    ist = pytz.timezone(CFG.timezone)
    now_ist = datetime.now(ist).isoformat()

    for idx, row in df.iterrows():
        if row["status"] != "OPEN":
            continue
        sym = row["symbol"]
        if sym not in market_data:
            continue
        candles = market_data[sym]
        if candles.empty:
            continue
        entry_t = pd.to_datetime(row["timestamp_ist"])
        # Compare on naive (drop tz) to avoid mismatch
        try:
            future = candles[candles.index > entry_t]
        except TypeError:
            future = candles[candles.index.tz_localize(None) > entry_t.tz_localize(None)]
        if future.empty:
            continue
        side = row["side"]
        entry = float(row["entry"]); sl = float(row["sl"])
        tp1 = float(row["tp1"]); tp2 = float(row["tp2"])
        risk = abs(entry - sl)

        hit_status, hit_price, hit_time, result_r = None, None, None, 0.0
        for ts, c in future.iterrows():
            hi, lo = float(c["high"]), float(c["low"])
            if side == "LONG":
                # SL hit?
                if lo <= sl:
                    hit_status = "SL_HIT"; hit_price = sl; result_r = -1.0; hit_time = ts; break
                if hi >= tp2:
                    hit_status = "TP2_HIT"; hit_price = tp2
                    result_r = (tp2 - entry) / risk; hit_time = ts; break
            else:
                if hi >= sl:
                    hit_status = "SL_HIT"; hit_price = sl; result_r = -1.0; hit_time = ts; break
                if lo <= tp2:
                    hit_status = "TP2_HIT"; hit_price = tp2
                    result_r = (entry - tp2) / risk; hit_time = ts; break

        # Expire after 1 trading day (24h) if no hit
        if hit_status is None:
            last_ts = future.index[-1]
            try:
                hours_open = (last_ts - entry_t).total_seconds() / 3600
            except TypeError:
                hours_open = (last_ts.tz_localize(None) - entry_t.tz_localize(None)).total_seconds() / 3600
            if hours_open >= 24:
                last_close = float(future.iloc[-1]["close"])
                hit_status = "EXPIRED"; hit_price = last_close
                hit_time = last_ts
                result_r = ((last_close - entry) if side == "LONG" else (entry - last_close)) / risk

        if hit_status:
            df.at[idx, "status"] = hit_status
            df.at[idx, "exit_price"] = f"{hit_price:.5f}"
            df.at[idx, "exit_time_ist"] = str(hit_time)
            df.at[idx, "result_r"] = f"{result_r:.2f}"
            risk_usd = float(row["risk_usd"]) if row["risk_usd"] else 0.0
            df.at[idx, "result_usd"] = f"{result_r * risk_usd:.2f}"
            df.at[idx, "closed_at_ist"] = now_ist
            updated += 1

    if updated:
        save_log(df)
    return updated


def trades_today() -> pd.DataFrame:
    df = load_log()
    if df.empty:
        return df
    df["timestamp_ist"] = pd.to_datetime(df["timestamp_ist"])
    today = datetime.now(pytz.timezone(CFG.timezone)).date()
    return df[df["timestamp_ist"].dt.date == today]


def stats_summary(df: Optional[pd.DataFrame] = None) -> Dict:
    if df is None:
        df = load_log()
    closed = df[df["status"].isin(["TP1_HIT", "TP2_HIT", "SL_HIT", "EXPIRED"])]
    if closed.empty:
        return {"total": 0, "wins": 0, "losses": 0, "winrate": 0,
                "total_r": 0, "total_usd": 0, "open": (df["status"] == "OPEN").sum()}
    closed = closed.copy()
    closed["result_r"]   = closed["result_r"].astype(float)
    closed["result_usd"] = closed["result_usd"].astype(float)
    wins = (closed["result_r"] > 0).sum()
    losses = (closed["result_r"] <= 0).sum()
    return {
        "total":     len(closed),
        "wins":      int(wins),
        "losses":    int(losses),
        "winrate":   round(wins / len(closed) * 100, 1),
        "total_r":   round(closed["result_r"].sum(), 2),
        "total_usd": round(closed["result_usd"].sum(), 2),
        "open":      int((df["status"] == "OPEN").sum()),
    }
