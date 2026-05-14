"""Data fetcher for OHLCV. Primary: yfinance. Robust to weekend/holiday.

For best-quality intraday data on a free tier, yfinance with GC=F (Gold
futures) gives ~60 days of 15m candles. That's more than enough to compute
EMA200/CPR/etc. and produce live signals.

If yfinance fails (rate-limited), we fall back to Twelve Data if a key is set
in env var TWELVE_DATA_API_KEY.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import yfinance as yf
import pytz

from .config import CFG

log = logging.getLogger(__name__)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase columns, ensure tz-aware index in IST, sorted."""
    df = df.copy()
    # yfinance may return MultiIndex columns when downloading a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep]
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(pytz.timezone(CFG.timezone))
    df = df.sort_index()
    df = df.dropna()
    return df


def fetch_yf(symbol: str, interval: str = "15m", days: int = 30) -> pd.DataFrame:
    """Fetch OHLC via yfinance."""
    period = f"{min(days, 59)}d"  # yfinance caps intraday history at 60d
    log.info("yfinance download %s interval=%s period=%s", symbol, interval, period)
    df = yf.download(
        symbol,
        interval=interval,
        period=period,
        progress=False,
        auto_adjust=False,
        prepost=False,
        threads=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned empty for {symbol}")
    return _normalize(df)


def fetch_twelve_data(symbol: str = "XAU/USD", interval: str = "15min",
                     outputsize: int = 2000) -> pd.DataFrame:
    """Fallback: Twelve Data API (needs TWELVE_DATA_API_KEY)."""
    api_key = os.getenv("TWELVE_DATA_API_KEY", "")
    if not api_key:
        raise RuntimeError("TWELVE_DATA_API_KEY not set")
    url = "https://api.twelvedata.com/time_series"
    r = requests.get(url, params={
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "values" not in data:
        raise RuntimeError(f"Twelve Data error: {data}")
    rows = data["values"]
    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").astype(float)
    return _normalize(df)


def fetch_ohlc(interval: Optional[str] = None) -> pd.DataFrame:
    """Smart fetch with fallback chain."""
    interval = interval or CFG.timeframe
    try:
        df = fetch_yf(CFG.symbol_yf, interval=interval, days=CFG.history_days)
        if len(df) >= 250:
            return df
        log.warning("yfinance returned only %d rows, trying fallback", len(df))
    except Exception as e:
        log.warning("yfinance failed: %s", e)

    # Fallback
    try:
        td_interval = {"15m": "15min", "5m": "5min", "1h": "1h", "1d": "1day"}.get(interval, "15min")
        df = fetch_twelve_data(CFG.symbol_td, interval=td_interval)
        return df
    except Exception as e:
        log.error("All data sources failed: %s", e)
        raise


def fetch_daily(symbol: Optional[str] = None, days: int = 365) -> pd.DataFrame:
    """Daily candles for prior-day high/low/close."""
    symbol = symbol or CFG.symbol_yf
    df = yf.download(symbol, interval="1d", period=f"{days}d", progress=False,
                     auto_adjust=False, threads=False)
    return _normalize(df)


def fetch_macro_snapshot() -> dict:
    """Return latest price + 1-day change for each macro symbol."""
    out = {}
    for name, sym in CFG.macro_symbols.items():
        try:
            df = yf.download(sym, period="5d", interval="1d", progress=False,
                            auto_adjust=False, threads=False)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            last = float(df["close"].iloc[-1])
            prev = float(df["close"].iloc[-2]) if len(df) >= 2 else last
            change_pct = (last - prev) / prev * 100 if prev else 0
            out[name] = {"price": last, "change_pct": change_pct, "symbol": sym}
        except Exception as e:
            log.warning("macro fetch failed for %s: %s", name, e)
    return out
