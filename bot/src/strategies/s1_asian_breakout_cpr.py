"""Strategy 1 — Asian Range Breakout + CPR Confluence."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .. import indicators as ind
from . import Signal


NAME = "Asian Breakout + CPR"
SID = "S1"

# Defaults (tune to taste)
ASIAN_START = "03:30"
ASIAN_END = "12:30"
LONDON_START_HOUR = 12  # IST
LONDON_END_HOUR = 16
MAX_CPR_WIDTH_PCT = 0.6
SL_BUFFER_ATR = 0.2
TP1_R = 1.0
TP2_R = 2.0


def check(df: pd.DataFrame, daily: pd.DataFrame, symbol: str) -> Optional[Signal]:
    """Return Signal if entry condition true on the LAST closed bar."""
    if len(df) < 60 or len(daily) < 2:
        return None

    bar = df.iloc[-1]
    prev_bar = df.iloc[-2]
    ts = df.index[-1]

    # London session window check
    if not (LONDON_START_HOUR <= ts.hour < LONDON_END_HOUR):
        return None

    # Asian range for today
    asian_h, asian_l = ind.session_range(df, ASIAN_START, ASIAN_END)
    if asian_h is None:
        return None

    # CPR from previous day's daily candle
    p_d = daily.iloc[-2]
    cpr = ind.compute_cpr(float(p_d["high"]), float(p_d["low"]), float(p_d["close"]),
                          float(bar["close"]))
    if cpr.width_pct > MAX_CPR_WIDTH_PCT:
        return None

    a = ind.atr(df, 14).iloc[-1]
    ema50 = ind.ema(df["close"], 50).iloc[-1]
    close = float(bar["close"])

    # Long: cross above asian_h + above TC + above EMA50
    crossed_up = float(prev_bar["close"]) <= asian_h and close > asian_h
    if crossed_up and close > cpr.tc and close > ema50:
        sl = asian_l - a * SL_BUFFER_ATR
        risk = close - sl
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="LONG",
            entry=close, sl=sl, tp1=close + risk * TP1_R, tp2=close + risk * TP2_R,
            reason=f"Broke Asian High {asian_h:.2f} | above CPR-TC {cpr.tc:.2f} | EMA50 OK",
            bar_time=ts,
        )

    crossed_dn = float(prev_bar["close"]) >= asian_l and close < asian_l
    if crossed_dn and close < cpr.bc and close < ema50:
        sl = asian_h + a * SL_BUFFER_ATR
        risk = sl - close
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="SHORT",
            entry=close, sl=sl, tp1=close - risk * TP1_R, tp2=close - risk * TP2_R,
            reason=f"Broke Asian Low {asian_l:.2f} | below CPR-BC {cpr.bc:.2f} | EMA50 OK",
            bar_time=ts,
        )
    return None
