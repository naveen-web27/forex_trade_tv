"""Strategy 4 — Opening Range Breakout (first 15-min of London)."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .. import indicators as ind
from . import Signal


NAME = "Opening Range Breakout"
SID = "S4"

ORB_START = "12:30"  # London open (IST)
ORB_END = "12:45"
TRADE_END_HOUR = 16
SL_BUFFER_ATR = 0.2
MIN_RANGE_ATR = 0.5
TP1_R = 1.5
TP2_R = 3.0


def check(df: pd.DataFrame, daily: pd.DataFrame, symbol: str) -> Optional[Signal]:
    if len(df) < 220:
        return None

    bar = df.iloc[-1]
    prev_bar = df.iloc[-2]
    ts = df.index[-1]

    # Trade only after ORB end and before TRADE_END_HOUR
    if ts.hour < 13 or ts.hour >= TRADE_END_HOUR:
        return None

    orb_h, orb_l = ind.session_range(df, ORB_START, ORB_END)
    if orb_h is None:
        return None

    a = ind.atr(df, 14).iloc[-1]
    ema200 = ind.ema(df["close"], 200).iloc[-1]
    close = float(bar["close"])

    if (orb_h - orb_l) < a * MIN_RANGE_ATR:
        return None

    if float(prev_bar["close"]) <= orb_h and close > orb_h and close > ema200:
        sl = orb_l - a * SL_BUFFER_ATR
        risk = close - sl
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="LONG",
            entry=close, sl=sl, tp1=close + risk * TP1_R, tp2=close + risk * TP2_R,
            reason=f"ORB high break {orb_h:.2f} | trend up",
            bar_time=ts,
        )
    if float(prev_bar["close"]) >= orb_l and close < orb_l and close < ema200:
        sl = orb_h + a * SL_BUFFER_ATR
        risk = sl - close
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="SHORT",
            entry=close, sl=sl, tp1=close - risk * TP1_R, tp2=close - risk * TP2_R,
            reason=f"ORB low break {orb_l:.2f} | trend down",
            bar_time=ts,
        )
    return None
