"""Strategy 2 — Previous Day High/Low Breakout + CPR direction filter."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .. import indicators as ind
from . import Signal


NAME = "PDH/PDL + CPR"
SID = "S2"

SESSION_START_HOUR = 12
SESSION_END_HOUR = 22
SL_ATR_MULT = 1.0
TP1_R = 1.0
TP2_R = 2.0


def check(df: pd.DataFrame, daily: pd.DataFrame, symbol: str) -> Optional[Signal]:
    if len(df) < 60 or len(daily) < 2:
        return None

    bar = df.iloc[-1]
    prev_bar = df.iloc[-2]
    ts = df.index[-1]
    if not (SESSION_START_HOUR <= ts.hour < SESSION_END_HOUR):
        return None

    p_d = daily.iloc[-2]
    pdh, pdl, pdc = float(p_d["high"]), float(p_d["low"]), float(p_d["close"])
    cpr = ind.compute_cpr(pdh, pdl, pdc, float(bar["close"]))
    a = ind.atr(df, 14).iloc[-1]
    ema50 = ind.ema(df["close"], 50).iloc[-1]
    close = float(bar["close"])

    crossed_up = float(prev_bar["close"]) <= pdh and close > pdh
    if crossed_up and close > cpr.pivot and close > ema50:
        sl = close - a * SL_ATR_MULT
        risk = close - sl
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="LONG",
            entry=close, sl=sl, tp1=close + risk * TP1_R, tp2=close + risk * TP2_R,
            reason=f"Broke PDH {pdh:.2f} | above Pivot {cpr.pivot:.2f}",
            bar_time=ts,
        )

    crossed_dn = float(prev_bar["close"]) >= pdl and close < pdl
    if crossed_dn and close < cpr.pivot and close < ema50:
        sl = close + a * SL_ATR_MULT
        risk = sl - close
        return Signal(
            strategy=SID, name=NAME, symbol=symbol, side="SHORT",
            entry=close, sl=sl, tp1=close - risk * TP1_R, tp2=close - risk * TP2_R,
            reason=f"Broke PDL {pdl:.2f} | below Pivot {cpr.pivot:.2f}",
            bar_time=ts,
        )
    return None
