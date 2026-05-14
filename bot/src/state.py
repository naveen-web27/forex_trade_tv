"""State helper: deduplicate signals across GitHub Actions runs.

We commit a tiny JSON file (state/signals_seen.json) back to the repo each
run, listing dedupe keys we've already alerted. This prevents duplicate
Telegram messages when cron overlaps a candle.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Set

from .config import CFG


def _path() -> Path:
    p = Path(CFG.state_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_seen() -> Set[str]:
    p = _path()
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text() or "[]")
        return set(data[-500:])  # cap memory
    except Exception:
        return set()


def save_seen(seen: Set[str]) -> None:
    p = _path()
    # Keep last 500 to limit growth
    arr = list(seen)[-500:]
    p.write_text(json.dumps(arr, indent=0))
