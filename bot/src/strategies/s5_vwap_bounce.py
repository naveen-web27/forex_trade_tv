"""Strategy 5 — VWAP Bounce in trend."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .. import indicators as ind
from . import Signal


NAME = "VWAP Bounce"
SID = "S5"

SESSION_START_HOUR = 12
SESSION_END_HOUR = 22
VWAP_PROX_ATR = 0.4
SL_BUFFER_ATR = 0.5
TP1_R = 1.0
TP2_R = 2.0


def _bullish_pinbar(row, prev_row, vwap_v) -> bool:
    rng = row["high"] - row["low"]
    if rng <= 0:
        return False
    body = abs(row["close"] - row["open"])
    return (row["close"] > row["open"]
            and row["low"] <= vwap_v
            and row["close"] > vwap_v
            and body > rng * 0.4)


def _bearish_pinbar(row, prev_row, vwap_v) -> bool:
    rng = row["high"] - row["low"]
    if rng <= 0:
        return False
    body = abs(row["close"] - row["open"])
    return (row["close"] < row["open"]
            and row["high"] >= vwap_v
            and row["close"] < vwap_v
            and body > rng * 0.4)


def check(df: pd.DataFrame, daily: pd.DataFrame, symbol: str) -> Optional[Signal]:
    if len(df) < 220:
        return None
    ts = df.index[-1]
    if not (SESSION_START_HOUR <= ts.hour < SESSION_END_HOUR):
        return None

    bar = df.iloc[-1]
    prev_bar = df.iloc[-2]
    close = float(bar["close"])
    a = ind.atr(df, 14).iloc[-1]
    ema200 = ind.ema(df["close"], 200).iloc[-1]
    vwap_s = ind.vwap_session(df)
    v = float(vwap_s.iloc[-1])
    r = ind.rsi(df["close"], 14).iloc[-1]

    if abs(close - v) > a * VWAP_PROX_ATR:
        return None

    if close > ema200 and 40 < r < 65 and _bullish_pinbar(bar, prev_bar, v):
        sl = v - a * SL_BUFFER_ATR
        risk = close - sl
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="LONG",
            entry=close, sl=sl, tp1=close + risk * TP1_R, tp2=close + risk * TP2_R,
            reason=f"Bullish pinbar at VWAP {v:.2f} | trend up | RSI {r:.0f}",
            bar_time=ts,
        )
    if close < ema200 and 35 < r < 60 and _bearish_pinbar(bar, prev_bar, v):
        sl = v + a * SL_BUFFER_ATR
        risk = sl - close
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="SHORT",
            entry=close, sl=sl, tp1=close - risk * TP1_R, tp2=close - risk * TP2_R,
            reason=f"Bearish pinbar at VWAP {v:.2f} | trend down | RSI {r:.0f}",
            bar_time=ts,
        )
    return None
