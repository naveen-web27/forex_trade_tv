"""Signal scanner — entry point for the every-15-min GitHub Actions workflow."""
from __future__ import annotations

import importlib
import logging
import sys

from src import data, news, telegram_notify, state
from src.config import CFG
from src.formatters import signal_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_signals")


def main() -> int:
    log.info("=== Signal scan start ===")

    # 1) Skip if red news active
    try:
        if news.red_news_active(buffer_minutes=30):
            log.info("Red news active — skipping signal scan.")
            return 0
    except Exception as e:
        log.warning("News check failed (continuing): %s", e)

    # 2) Fetch data
    try:
        df = data.fetch_ohlc()
        daily = data.fetch_daily(days=20)
    except Exception as e:
        log.error("Data fetch failed: %s", e)
        return 1
    log.info("Fetched %d intraday candles, %d daily candles", len(df), len(daily))

    # 3) Run each enabled strategy
    seen = state.load_seen()
    new_seen = set(seen)
    sent = 0

    for strat_name in CFG.enable_strategies:
        try:
            mod = importlib.import_module(f"src.strategies.{strat_name}")
            sig = mod.check(df, daily, CFG.symbol_display)
            if sig is None:
                log.info("[%s] no signal", strat_name)
                continue
            key = sig.dedupe_key()
            if key in seen:
                log.info("[%s] signal already alerted (%s)", strat_name, key)
                continue
            text = signal_message(sig, CFG.account_size_usd, CFG.risk_pct)
            if telegram_notify.send(text):
                log.info("[%s] ALERT SENT: %s %s @ %.2f",
                         strat_name, sig.side, sig.symbol, sig.entry)
                new_seen.add(key)
                sent += 1
            else:
                log.error("[%s] Telegram send failed", strat_name)
        except Exception as e:
            log.exception("[%s] error: %s", strat_name, e)

    state.save_seen(new_seen)
    log.info("=== Signal scan done. Sent: %d ===", sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
