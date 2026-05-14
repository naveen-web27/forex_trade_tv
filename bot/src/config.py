"""Central configuration for the bot."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


# ─────────── Telegram (loaded from GitHub Secrets / env) ───────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")


# ─────────── Trading config ───────────
@dataclass
class Settings:
    # Primary pair. Yahoo tickers:
    #   "GC=F"     = Gold Futures (best free intraday data for XAUUSD proxy)
    #   "XAUUSD=X" = FX spot gold (less reliable intraday)
    # Twelve Data symbol for fallback = "XAU/USD"
    symbol_yf: str = "GC=F"
    symbol_td: str = "XAU/USD"
    symbol_display: str = "XAUUSD"

    timeframe: str = "15m"          # yfinance interval
    history_days: int = 30          # candles to fetch
    account_size_usd: float = 10_000
    risk_pct: float = 0.5           # % per trade
    timezone: str = "Asia/Kolkata"

    # Enable/disable strategies
    enable_strategies: List[str] = field(default_factory=lambda: [
        "s1_asian_breakout_cpr",
        "s2_pdh_pdl_cpr",
        "s3_smc_sweep_fvg",
        "s4_orb",
        "s5_vwap_bounce",
    ])

    # Macro symbols for the morning brief
    macro_symbols: dict = field(default_factory=lambda: {
        "DXY (Dollar Index)":  "DX-Y.NYB",
        "US 10Y Yield":        "^TNX",
        "Gold (XAUUSD proxy)": "GC=F",
        "S&P 500":             "^GSPC",
        "Crude Oil":           "CL=F",
        "Bitcoin":             "BTC-USD",
    })

    # ForexFactory weekly calendar — free, no key needed
    ff_calendar_url: str = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

    # State file path (used to dedupe signals across runs)
    state_file: str = "bot/state/signals_seen.json"


CFG = Settings()
