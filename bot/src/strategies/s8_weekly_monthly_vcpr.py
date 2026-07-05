"""Strategy S8 — Weekly & Monthly Virgin CPR Scanner.

Same logic as S7 (daily VCPR) but applied to weekly and monthly bars.

  Weekly  VCPR (~1–2 per month per pair)  — strong HTF magnet zones
  Monthly VCPR (~1–2 per quarter per pair) — very strong, institutional levels

Touch detection:
  Weekly  CPR: checked against weekly  bars (same timeframe as the band)
  Monthly CPR: checked against monthly bars (same timeframe as the band)

Returns via check():
  {
    "weekly":  [(date, bcpr, tcpr, width), ...],
    "monthly": [(date, bcpr, tcpr, width), ...],
  }
  Each list is sorted newest date first. Empty list if no virgins found.
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
from tvDatafeed import TvDatafeed, Interval

log = logging.getLogger(__name__)

NAME = "Weekly/Monthly Virgin CPR"
SID  = "S8"

# ── shared TvDatafeed instance ────────────────────────────────────────────────
_tv = TvDatafeed()

# ── tunables ──────────────────────────────────────────────────────────────────
WEEKLY_BARS  = 52   # ~1 year of weekly data
MONTHLY_BARS = 24   # ~2 years of monthly data


# ─────────────────────────────────────────────────────────────────────────────
# Core CPR helpers  (identical logic to S7)
# ─────────────────────────────────────────────────────────────────────────────

def _cal_cpr(df: pd.DataFrame) -> pd.DataFrame:
    """Add PP, BCPR, TCPR columns using previous-bar's H/L/C."""
    df = df.copy()
    for i in range(1, len(df)):
        ph = df.loc[i - 1, "high"]
        pl = df.loc[i - 1, "low"]
        pc = df.loc[i - 1, "close"]
        pp = (ph + pl + pc) / 3.0
        bc = (ph + pl) / 2.0
        tc = (pp - bc) + pp
        df.loc[i, "PP"]   = pp
        df.loc[i, "BCPR"] = min(bc, tc)
        df.loc[i, "TCPR"] = max(bc, tc)
    return df


def _find_virgin(df: pd.DataFrame) -> list[tuple]:
    """
    Scan for virgin CPR bands.
    A band is virgin if no bar AFTER the band's creation bar has touched it.
    Touch: bar_high >= BCPR  AND  bar_low <= TCPR
    Returns list of (date_str, bcpr, tcpr, width) sorted newest first.
    """
    virgins = []
    for i in range(1, len(df) - 1):      # skip row 0 (no CPR) and last row (current)
        bcpr = df.loc[i, "BCPR"]
        tcpr = df.loc[i, "TCPR"]
        if pd.isna(bcpr) or pd.isna(tcpr):
            continue

        touched = False
        for j in range(i + 1, len(df)):  # only FUTURE bars
            if df.loc[j, "high"] >= bcpr and df.loc[j, "low"] <= tcpr:
                touched = True
                break

        if not touched:
            date_val = df.loc[i, "datetime"]
            virgins.append((
                str(date_val)[:10],   # "YYYY-MM-DD"
                float(bcpr),
                float(tcpr),
                float(abs(tcpr - bcpr)),
            ))

    virgins.sort(key=lambda x: x[0], reverse=True)  # newest first
    return virgins


def _fetch_and_scan(symbol: str, exchange: str, interval: Interval, n_bars: int) -> list[tuple]:
    """Fetch bars, compute CPR, find virgin bands, return tuple list."""
    raw = _tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
    if raw is None or raw.empty:
        raise ValueError(f"No data for {exchange}:{symbol} @ {interval}")

    raw = raw.reset_index()
    raw.columns = [c.lower() for c in raw.columns]

    # tvDatafeed index name varies; normalise to 'datetime'
    if "datetime" not in raw.columns:
        # after reset_index the old index appears as first column; rename it
        raw.rename(columns={raw.columns[0]: "datetime"}, inplace=True)

    raw = raw[["datetime", "open", "high", "low", "close"]].dropna(
        subset=["high", "low", "close"]
    ).reset_index(drop=True)

    cpr_df = _cal_cpr(raw)
    return _find_virgin(cpr_df)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def check(
    symbol: str,
    exchange: str = "FX",
    retries: int = 5,
) -> dict[str, list[tuple]]:
    """
    Scan weekly and monthly bars for virgin CPR bands.

    Returns
    -------
    {
      "weekly":  [(date_str, bcpr, tcpr, width), ...],
      "monthly": [(date_str, bcpr, tcpr, width), ...],
    }
    Both lists are empty on failure (never raises).
    """
    result: dict[str, list[tuple]] = {"weekly": [], "monthly": []}

    for timeframe, interval, n_bars, key in [
        ("weekly",  Interval.in_weekly,  WEEKLY_BARS,  "weekly"),
        ("monthly", Interval.in_monthly, MONTHLY_BARS, "monthly"),
    ]:
        for attempt in range(retries):
            try:
                result[key] = _fetch_and_scan(symbol, exchange, interval, n_bars)
                log.info("[%s] %s VCPR: %d virgin band(s)", symbol, timeframe, len(result[key]))
                break
            except Exception as exc:
                log.warning(
                    "[%s] %s fetch attempt %d/%d: %s",
                    symbol, timeframe, attempt + 1, retries, exc,
                )

    return result
