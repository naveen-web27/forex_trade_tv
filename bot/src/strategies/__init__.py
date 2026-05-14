"""Common dataclass + helpers for strategy results."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Signal:
    strategy: str           # short id, e.g. "S1"
    name: str               # full name
    symbol: str
    side: str               # "LONG" / "SHORT"
    entry: float
    sl: float
    tp1: float
    tp2: float
    reason: str
    bar_time: datetime      # bar timestamp (IST)

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry - self.sl)

    @property
    def rr1(self) -> float:
        return abs(self.tp1 - self.entry) / self.risk_per_unit if self.risk_per_unit else 0

    @property
    def rr2(self) -> float:
        return abs(self.tp2 - self.entry) / self.risk_per_unit if self.risk_per_unit else 0

    def dedupe_key(self) -> str:
        """Unique key per signal so we don't alert twice across runs."""
        return f"{self.strategy}|{self.symbol}|{self.side}|{self.bar_time.isoformat()}"
