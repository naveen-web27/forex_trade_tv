"""Position sizing helper.

risk_usd = account * risk_pct/100
lot_size = risk_usd / (sl_dist_in_price * pip_value_per_lot)

Returns (lot_size_rounded, risk_usd).
"""
from __future__ import annotations

import math

from .config import CFG, PAIRS, PairConfig


def get_pair(display: str) -> PairConfig | None:
    for p in PAIRS:
        if p.display == display:
            return p
    return None


def compute_size(symbol: str, entry: float, sl: float) -> tuple[float, float]:
    pair = get_pair(symbol)
    if pair is None:
        # default = XAUUSD assumption
        pip_val = 100.0
    else:
        pip_val = pair.pip_value_per_lot

    risk_usd = CFG.account_size_usd * CFG.risk_pct / 100
    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return 0.0, 0.0
    lots = risk_usd / (sl_dist * pip_val)
    # Round down to 2 decimals (broker min usually 0.01)
    lots = max(0.01, math.floor(lots * 100) / 100)
    return lots, risk_usd
