"""Signal scanner — multi-pair, every 15 min.

For each enabled pair × each strategy:
  1. Fetch OHLC
  2. Run strategy.check() on last closed bar
  3. If signal → compute lot size, send to Telegram, append to trade CSV
  4. Skip if red news within ±30 min
"""
from __future__ import annotations

import importlib
import logging
import sys

from src import data, news, telegram_notify, state, trade_log, position_size
from src.config import CFG, PAIRS
from src.formatters import signal_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_signals")


def fetch_for_pair(pair) -> tuple:
    df = data.fetch_yf(pair.yf_symbol, interval=CFG.timeframe, days=CFG.history_days)
    daily = data.fetch_daily(pair.yf_symbol, days=20)
    return df, daily


def main() -> int:
    log.info("=== Multi-pair signal scan start ===")

    # 1) Red news filter
    try:
        if news.red_news_active(buffer_minutes=30):
            log.info("Red news active — skipping signal scan.")
            return 0
    except Exception as e:
        log.warning("News check failed (continuing): %s", e)

    seen = state.load_seen()
    new_seen = set(seen)
    sent = 0

    for pair in PAIRS:
        if not pair.enabled:
            continue
        log.info("─── %s ───", pair.display)
        try:
            df, daily = fetch_for_pair(pair)
        except Exception as e:
            log.warning("[%s] data fetch failed: %s", pair.display, e)
            continue
        if len(df) < 220 or len(daily) < 3:
            log.warning("[%s] not enough data (%d intraday, %d daily)",
                        pair.display, len(df), len(daily))
            continue

        for strat_name in CFG.enable_strategies:
            try:
                mod = importlib.import_module(f"src.strategies.{strat_name}")
                sig = mod.check(df, daily, pair.display)
                if sig is None:
                    continue
                key = sig.dedupe_key()
                if key in seen:
                    log.info("[%s/%s] already alerted (%s)", pair.display, strat_name, key)
                    continue

                lots, risk_usd = position_size.compute_size(pair.display, sig.entry, sig.sl)
                text = signal_message(sig, CFG.account_size_usd, CFG.risk_pct,
                                      lot_size=lots, risk_usd=risk_usd)
                if telegram_notify.send(text):
                    trade_log.append_signal(sig, lots, risk_usd)
                    new_seen.add(key)
                    sent += 1
                    log.info("[%s/%s] ✅ SENT %s @ %.4f (%.2f lots)",
                             pair.display, strat_name, sig.side, sig.entry, lots)
                else:
                    log.error("[%s/%s] Telegram send failed", pair.display, strat_name)
            except Exception as e:
                log.exception("[%s/%s] error: %s", pair.display, strat_name, e)

    state.save_seen(new_seen)
    log.info("=== Done. Sent: %d ===", sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
