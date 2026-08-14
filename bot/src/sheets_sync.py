"""Publish VCPR state to Google Sheets through an Apps Script web app."""
from __future__ import annotations

import logging
import os
from typing import Any

import requests

log = logging.getLogger(__name__)

SHEETS_URL = os.getenv("VCPR_SHEETS_WEBHOOK_URL", "").strip()
SHEETS_API_KEY = os.getenv("VCPR_SHEETS_API_KEY", "").strip()
PROXIMITY_MIN_PIPS = 5.0
PROXIMITY_MAX_PIPS = 20.0


def _pip_size(symbol: str) -> float:
    symbol = symbol.upper()
    if "JPY" in symbol:
        return 0.01
    if "XAU" in symbol:
        return 0.10
    return 0.0001


def _distance(price: float | None, bcpr: float, tcpr: float, pip: float) -> tuple[float, str]:
    if price is None:
        return 0.0, "unknown"
    if price < bcpr:
        return (bcpr - price) / pip, "below"
    if price > tcpr:
        return (price - tcpr) / pip, "above"
    return 0.0, "inside"


def build_rows(tf_data: dict[str, dict[str, list[dict[str, Any]]]],
               prices: dict[str, float]) -> list[dict[str, Any]]:
    """Flatten scanner state into the stable row contract used by the sheet."""
    rows: list[dict[str, Any]] = []
    for timeframe, symbols in tf_data.items():
        for symbol, bands in symbols.items():
            price = prices.get(symbol)
            pip = _pip_size(symbol)
            for band in bands:
                distance, direction = _distance(
                    price, float(band["bcpr"]), float(band["tcpr"]), pip
                )
                alert = "NEAR" if PROXIMITY_MIN_PIPS <= distance <= PROXIMITY_MAX_PIPS else ""
                rows.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "vcprDate": str(band["date"])[:10],
                    "bcpr": float(band["bcpr"]),
                    "tcpr": float(band["tcpr"]),
                    "width": float(band.get("width", 0)),
                    "price": price if price is not None else "",
                    "distancePips": round(distance, 1),
                    "direction": direction,
                    "alert": alert,
                })
    return rows


def sync_rows(rows: list[dict[str, Any]], scan_time: str) -> bool:
    """Send a batch to Apps Script; no-op when GitHub secrets are not configured."""
    if not SHEETS_URL or not SHEETS_API_KEY:
        log.info("Google Sheets sync skipped: VCPR webhook secrets are not configured")
        return False
    try:
        response = requests.post(
            SHEETS_URL,
            json={"action": "syncVcpr", "apiKey": SHEETS_API_KEY,
                  "scanTime": scan_time, "rows": rows},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "ok":
            raise RuntimeError(result.get("message", "unknown Sheets error"))
        log.info("Synced %d VCPR rows to Google Sheets", len(rows))
        return True
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        log.error("Google Sheets sync failed: %s", exc)
        return False