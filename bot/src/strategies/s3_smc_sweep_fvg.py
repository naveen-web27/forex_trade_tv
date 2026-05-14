"""Strategy 3 — SMC: Liquidity Sweep + FVG retest."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .. import indicators as ind
from . import Signal


NAME = "SMC Sweep + FVG"
SID = "S3"

SESSION_START_HOUR = 12
SESSION_END_HOUR = 22
SWING_LEFT = 10
SWING_RIGHT = 10
FVG_MIN_ATR = 0.3
FVG_LOOKBACK = 40
SWEEP_LOOKBACK = 10
SL_BUFFER_ATR = 0.3
TP1_R = 1.0
TP2_R = 2.5


def check(df: pd.DataFrame, daily: pd.DataFrame, symbol: str) -> Optional[Signal]:
    if len(df) < 220:
        return None

    bar = df.iloc[-1]
    ts = df.index[-1]
    if not (SESSION_START_HOUR <= ts.hour < SESSION_END_HOUR):
        return None

    close = float(bar["close"])
    a = ind.atr(df, 14).iloc[-1]
    ema200 = ind.ema(df["close"], 200).iloc[-1]

    swing_h, swing_l = ind.last_swing_levels(df, SWING_LEFT, SWING_RIGHT)
    bear_sweep, bull_sweep = ind.detect_sweep(df.iloc[:-1], swing_h, swing_l,
                                              lookback=SWEEP_LOOKBACK)

    bull_fvg, bear_fvg = ind.find_recent_fvgs(df, FVG_MIN_ATR, FVG_LOOKBACK)

    # LONG: a recent bullish sweep occurred AND price is retesting a bull FVG from above
    if bull_sweep and bull_fvg and close > ema200:
        low_ = float(bar["low"])
        if bull_fvg.bot <= low_ <= bull_fvg.top and close > bull_fvg.bot:
            sl = bull_fvg.bot - a * SL_BUFFER_ATR
            risk = close - sl
            return Signal(
                strategy=SID, name=NAME, symbol=symbol, side="LONG",
                entry=close, sl=sl, tp1=close + risk * TP1_R, tp2=close + risk * TP2_R,
                reason=f"Bullish liq sweep of {swing_l:.2f} + bull-FVG retest [{bull_fvg.bot:.2f}-{bull_fvg.top:.2f}]",
                bar_time=ts,
            )

    if bear_sweep and bear_fvg and close < ema200:
        high_ = float(bar["high"])
        if bear_fvg.bot <= high_ <= bear_fvg.top and close < bear_fvg.top:
            sl = bear_fvg.top + a * SL_BUFFER_ATR
            risk = sl - close
            return Signal(
                strategy=SID, name=NAME, symbol=symbol, side="SHORT",
                entry=close, sl=sl, tp1=close - risk * TP1_R, tp2=close - risk * TP2_R,
                reason=f"Bearish liq sweep of {swing_h:.2f} + bear-FVG retest [{bear_fvg.bot:.2f}-{bear_fvg.top:.2f}]",
                bar_time=ts,
            )
    return None
