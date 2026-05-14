"""Technical indicators + structure detection (pure pandas, no TA-Lib needed)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


# ─────────── Basic indicators ───────────

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def vwap_session(df: pd.DataFrame) -> pd.Series:
    """Anchored VWAP that resets each calendar day (using df.index date)."""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].replace(0, 1)  # XAUUSD spot may have 0 volume
    grp = df.index.date
    cum_pv = pd.Series(tp.values * vol.values, index=df.index).groupby(grp).cumsum()
    cum_v = vol.groupby(grp).cumsum()
    return cum_pv / cum_v


# ─────────── CPR (Daily) ───────────

@dataclass
class CPR:
    pivot: float
    tc: float
    bc: float
    width_pct: float  # (top-bot)/price *100


def compute_cpr(pdh: float, pdl: float, pdc: float, current_price: float) -> CPR:
    pivot = (pdh + pdl + pdc) / 3
    bc = (pdh + pdl) / 2
    tc = (pivot - bc) + pivot
    top, bot = max(tc, bc), min(tc, bc)
    width = (top - bot) / current_price * 100 if current_price else 0
    return CPR(pivot=pivot, tc=top, bc=bot, width_pct=width)


# ─────────── Asian / Session range ───────────

def session_range(df: pd.DataFrame, start_hhmm: str, end_hhmm: str) -> tuple[Optional[float], Optional[float]]:
    """Return (high, low) of bars between start and end (IST hh:mm) for the LATEST date in df."""
    if df.empty:
        return None, None
    sh, sm = map(int, start_hhmm.split(":"))
    eh, em = map(int, end_hhmm.split(":"))
    last_date = df.index[-1].date()
    today = df[df.index.date == last_date]
    start = today.index.normalize()[0].replace(hour=sh, minute=sm)
    end = today.index.normalize()[0].replace(hour=eh, minute=em)
    seg = today[(today.index >= start) & (today.index <= end)]
    if seg.empty:
        return None, None
    return float(seg["high"].max()), float(seg["low"].min())


# ─────────── Swing pivots ───────────

def pivot_high(series: pd.Series, left: int = 5, right: int = 5) -> pd.Series:
    """True at index i if series[i] is the max of [i-left, i+right]."""
    win = series.rolling(left + right + 1, center=True).max()
    return (series == win) & series.notna()


def pivot_low(series: pd.Series, left: int = 5, right: int = 5) -> pd.Series:
    win = series.rolling(left + right + 1, center=True).min()
    return (series == win) & series.notna()


def last_swing_levels(df: pd.DataFrame, left: int = 10, right: int = 10) -> tuple[Optional[float], Optional[float]]:
    """Return (last_swing_high, last_swing_low) before current bar (offset by `right`)."""
    if len(df) < left + right + 5:
        return None, None
    ph = pivot_high(df["high"], left, right)
    pl = pivot_low(df["low"], left, right)
    sh = df.loc[ph, "high"]
    sl = df.loc[pl, "low"]
    return (float(sh.iloc[-1]) if not sh.empty else None,
            float(sl.iloc[-1]) if not sl.empty else None)


# ─────────── Fair Value Gap (3-bar imbalance) ───────────

@dataclass
class FVG:
    kind: str          # "bull" / "bear"
    top: float
    bot: float
    bar_index: int     # index in df


def find_recent_fvgs(df: pd.DataFrame, min_size_atr: float = 0.3,
                     lookback: int = 50) -> tuple[Optional[FVG], Optional[FVG]]:
    """Return (latest bull FVG, latest bear FVG) within `lookback` bars."""
    if len(df) < lookback + 3:
        return None, None
    a = atr(df, 14)
    bull, bear = None, None
    start = max(2, len(df) - lookback)
    for i in range(start, len(df)):
        size_thr = a.iloc[i] * min_size_atr
        # bullish FVG: low[i] > high[i-2]
        if df["low"].iloc[i] > df["high"].iloc[i - 2]:
            gap = df["low"].iloc[i] - df["high"].iloc[i - 2]
            if gap >= size_thr:
                bull = FVG("bull", top=float(df["low"].iloc[i]),
                           bot=float(df["high"].iloc[i - 2]), bar_index=i)
        # bearish FVG: high[i] < low[i-2]
        if df["high"].iloc[i] < df["low"].iloc[i - 2]:
            gap = df["low"].iloc[i - 2] - df["high"].iloc[i]
            if gap >= size_thr:
                bear = FVG("bear", top=float(df["low"].iloc[i - 2]),
                           bot=float(df["high"].iloc[i]), bar_index=i)
    return bull, bear


# ─────────── Liquidity Sweep ───────────

def detect_sweep(df: pd.DataFrame, swing_high: Optional[float],
                 swing_low: Optional[float], lookback: int = 5) -> tuple[bool, bool]:
    """Return (bearish_sweep_recently, bullish_sweep_recently) in last `lookback` bars."""
    if len(df) < lookback or swing_high is None or swing_low is None:
        return False, False
    recent = df.tail(lookback)
    # Bearish sweep: wick above swing_high but close below
    bear_sweep = ((recent["high"] > swing_high) & (recent["close"] < swing_high)).any()
    bull_sweep = ((recent["low"] < swing_low) & (recent["close"] > swing_low)).any()
    return bool(bear_sweep), bool(bull_sweep)
