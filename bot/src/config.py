"""Central configuration for the bot."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


# ─────────── Telegram credentials (hardcoded per user request) ───────────
# ⚠️ Keep this repo PRIVATE on GitHub — anyone with read access can use the bot.
TELEGRAM_BOT_TOKEN_DEFAULT = "7889376398:AAH7tMKhPHtt6NC75mMYvCgeV4bLtx2LwhA"
TELEGRAM_CHAT_ID_DEFAULT   = "-4929420131"

# Env vars override the defaults if set (handy for local testing)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN") or TELEGRAM_BOT_TOKEN_DEFAULT
TELEGRAM_CHAT_ID: str   = os.getenv("TELEGRAM_CHAT_ID")   or TELEGRAM_CHAT_ID_DEFAULT


# ─────────── Trading config ───────────
@dataclass
class PairConfig:
    """One tradable instrument."""
    display: str        # "XAUUSD"
    yf_symbol: str      # yfinance ticker
    td_symbol: str      # Twelve Data ticker (fallback)
    pip_value_per_lot: float  # $ per 1 unit move per 1 standard lot
    point_size: float   # smallest meaningful move (for display formatting)
    min_lot: float = 0.01
    enabled: bool = True


# All pairs to scan. Add/remove freely.
PAIRS: list = [
    PairConfig("XAUUSD",  "GC=F",       "XAU/USD",  100.0,  0.01),  # gold: $1 move on 1 lot = $100
    PairConfig("GBPUSD",  "GBPUSD=X",   "GBP/USD",  10.0,   0.0001),
    PairConfig("EURUSD",  "EURUSD=X",   "EUR/USD",  10.0,   0.0001),
    PairConfig("NAS100",  "NQ=F",       "NDX",      20.0,   0.25),  # Nasdaq futures
]


@dataclass
class Settings:
    # Primary pair (used by single-pair legacy scripts; multi-pair uses PAIRS list)
    symbol_yf: str = "GC=F"
    symbol_td: str = "XAU/USD"
    symbol_display: str = "XAUUSD"

    timeframe: str = "15m"
    history_days: int = 30
    account_size_usd: float = 5_000   # FundingPips challenge
    risk_pct: float = 0.3             # Start cautious; bump to 0.5 after passing challenge
    timezone: str = "Asia/Kolkata"

    enable_strategies: List[str] = field(default_factory=lambda: [
        "s1_asian_breakout_cpr",
        "s2_pdh_pdl_cpr",
        "s3_smc_sweep_fvg",
        "s4_orb",
        "s5_vwap_bounce",
    ])

    macro_symbols: dict = field(default_factory=lambda: {
        "DXY (Dollar Index)":  "DX-Y.NYB",
        "US 10Y Yield":        "^TNX",
        "Gold (XAUUSD proxy)": "GC=F",
        "S&P 500":             "^GSPC",
        "Crude Oil":           "CL=F",
        "Bitcoin":             "BTC-USD",
    })

    ff_calendar_url: str = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    state_file: str = "bot/state/signals_seen.json"
    trade_log_csv: str = "data/trades.csv"
    bt_report_path: str = "data/backtest_report.md"


CFG = Settings()
