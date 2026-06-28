"""Strategy 6 — Virgin CPR Scanner (Multi-Day, All Pairs).

Mirrors Pine Script Module D logic exactly:
  - Pivot  = (PDH + PDL + PDC) / 3
  - BC     = (PDH + PDL) / 2
  - TC     = 2 × Pivot − BC
  - Band   = [min(TC, BC), max(TC, BC)]
  - Virgin = no 1H candle since that day has touched the band
             (condition: candle_high >= band_bot AND candle_low <= band_top)
  - Wide   = band_width > ATR(14) × WIDE_FACTOR  →  strong magnet zone

This strategy does NOT produce a directional Signal on its own.
It is called by run_signals.py → vcpr_scan_all_pairs(), which:
  1. Runs check() on every pair to get the VCprReport
  2. Sends a consolidated Telegram summary once per session
  3. Appends results to a dedicated state file so repeats are suppressed

Returns:
  VCprReport  — always (even if empty), never None.
  The caller decides whether to alert based on .has_virgins.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import logging

import pandas as pd

from .. import indicators as ind   # same relative import as s2_pdh_pdl_cpr

log = logging.getLogger(__name__)

NAME  = "Virgin CPR"
SID   = "S6"

# ─── tunables ───────────────────────────────────────────────────────────────
LOOKBACK_DAYS  = 30      # how many past daily bars to inspect
WIDE_FACTOR    = 1.0     # band_width > WIDE_FACTOR × ATR(14)  →  wide CPR
ATR_PERIOD     = 14


# ─── data class ─────────────────────────────────────────────────────────────
@dataclass
class VirginBand:
    date:      str     # "YYYY-MM-DD"  — the day this CPR was active
    pivot:     float
    bc:        float
    tc:        float
    band_top:  float   # max(tc, bc)
    band_bot:  float   # min(tc, bc)
    width:     float   # band_top − band_bot
    atr14:     float
    is_wide:   bool
    is_virgin: bool = True

    @property
    def width_pct(self) -> float:
        return (self.width / self.pivot * 100) if self.pivot else 0.0

    @property
    def tag(self) -> str:
        return "🔴 WIDE" if self.is_wide else "🟣 Normal"

    def one_liner(self) -> str:
        return (
            f"{self.tag} | {self.date} | "
            f"Pivot {self.pivot:.5f} | "
            f"Band [{self.band_bot:.5f}–{self.band_top:.5f}] | "
            f"W={self.width_pct:.2f}%"
            + (" ⚠️ WIDE" if self.is_wide else "")
        )


@dataclass
class VCprReport:
    symbol:  str
    bands:   list[VirginBand] = field(default_factory=list)   # ALL virgin bands found

    @property
    def has_virgins(self) -> bool:
        return bool(self.bands)

    @property
    def wide_count(self) -> int:
        return sum(1 for b in self.bands if b.is_wide)

    @property
    def normal_count(self) -> int:
        return sum(1 for b in self.bands if not b.is_wide)

    def summary_lines(self) -> list[str]:
        """Return formatted lines for Telegram message (sorted newest first)."""
        lines = []
        for b in sorted(self.bands, key=lambda x: x.date, reverse=True):
            lines.append(f"  • {b.one_liner()}")
        return lines



# ─── internal helpers ────────────────────────────────────────────────────────
def _calc_atr(daily_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR via exponential smoothing of True Range — same as Pine ta.atr()."""
    df = daily_df.copy()
    prev = df["close"].shift(1)
    df["tr"] = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev).abs(),
        (df["low"]  - prev).abs(),
    ], axis=1).max(axis=1)
    return df["tr"].ewm(span=period, adjust=False).mean()


def _build_bands(daily_df: pd.DataFrame, lookback: int) -> list[VirginBand]:
    """
    Compute CPR bands for the last `lookback` completed days.
    Each band uses the PREVIOUS day's H/L/C (mirrors Pine: high[1], low[1], close[1]).
    """
    df = daily_df.reset_index(drop=True)
    atr_s = _calc_atr(df, ATR_PERIOD)
    bands: list[VirginBand] = []

    # We need row i-1 for H/L/C; row i just supplies the date label
    start = max(1, len(df) - lookback)
    for i in range(start, len(df)):
        prev = df.iloc[i - 1]
        ph, pl, pc = float(prev["high"]), float(prev["low"]), float(prev["close"])
        pivot     = (ph + pl + pc) / 3.0
        bc        = (ph + pl) / 2.0
        tc        = 2.0 * pivot - bc
        band_top  = max(tc, bc)
        band_bot  = min(tc, bc)
        width     = band_top - band_bot
        atr14     = float(atr_s.iloc[i - 1]) if i - 1 < len(atr_s) else 0.0
        is_wide   = (atr14 > 0) and (width > atr14 * WIDE_FACTOR)

        # Date label: use the index if it's a DatetimeIndex, else the 'date' column
        if hasattr(df.index, "strftime"):
            date_str = df.index[i].strftime("%Y-%m-%d")
        elif "date" in df.columns:
            date_str = str(df["date"].iloc[i])[:10]
        else:
            date_str = f"day-{i}"

        bands.append(VirginBand(
            date=date_str, pivot=pivot, bc=bc, tc=tc,
            band_top=band_top, band_bot=band_bot,
            width=width, atr14=atr14, is_wide=is_wide,
        ))
    return bands


def _mark_touched(bands: list[VirginBand], df_1h: pd.DataFrame) -> list[VirginBand]:
    """
    For each band, scan all 1H bars AFTER that date.
    Touch condition (Pine Module D):  high >= band_bot  AND  low <= band_top
    """
    for band in bands:
        # Resolve the date column — yfinance returns a DatetimeIndex
        if hasattr(df_1h.index, "strftime"):
            future = df_1h[df_1h.index.strftime("%Y-%m-%d") > band.date]
        elif "date" in df_1h.columns:
            future = df_1h[df_1h["date"].astype(str).str[:10] > band.date]
        else:
            future = df_1h   # fallback: can't filter, assume no touch

        if future.empty:
            continue   # no bars after that date → still virgin

        touched = (
            (future["high"] >= band.band_bot) &
            (future["low"]  <= band.band_top)
        ).any()
        band.is_virgin = not touched
    return bands


# ─── public API — called by run_signals.py ───────────────────────────────────
def check(
    df: pd.DataFrame,          # intraday (15m) bars — used for touch detection
    daily: pd.DataFrame,       # daily bars — at least LOOKBACK_DAYS + 2 rows
    symbol: str,
) -> Optional[VCprReport]:
    """
    Returns a VCprReport for this symbol.
    Returns None only if data is insufficient (caller should log and skip).
    """
    if len(daily) < LOOKBACK_DAYS + 2:
        log.warning("[%s] Not enough daily data for VCPR (%d rows)", symbol, len(daily))
        return None

    # Build all bands from daily data
    bands = _build_bands(daily, LOOKBACK_DAYS)

    # Touch-detection uses 1H bars.
    # In the existing repo, df is 15m. Resample to 1H for efficiency.
    try:
        df_1h = df["close high low".split()].resample("1h").agg({
            "close": "last",
            "high":  "max",
            "low":   "min",
        }).dropna()
    except Exception:
        df_1h = df   # if resample fails (flat index), use as-is

    bands = _mark_touched(bands, df_1h)
    virgin_bands = [b for b in bands if b.is_virgin]

    report = VCprReport(symbol=symbol, bands=virgin_bands)
    if report.has_virgins:
        log.info(
            "[%s] Virgin CPRs: %d total (%d wide, %d normal)",
            symbol, len(virgin_bands), report.wide_count, report.normal_count,
        )
    else:
        log.info("[%s] No virgin CPRs in last %d days", symbol, LOOKBACK_DAYS)

    return report