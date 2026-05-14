# 🚀 Forex Trading System — Full Automation

XAUUSD + multi-pair signal scanner running 24/5 on GitHub Actions → Telegram.

---

## 🤖 What runs automatically (all on GitHub Actions)

| Workflow | Time (IST) | What you receive on Telegram |
|----------|-----------|------------------------------|
| 🌅 **Morning Brief** | Mon–Fri 11:30 AM | Red news + DXY/yields/gold + key levels + bias |
| 📰 **News Watcher** | Every 30 min | Warning 30-90 min before red news |
| 📈 **Signal Scanner** | Every 15 min, market hours | Signals from 5 strategies × 4 pairs |
| 💬 **Commands** | Every 5 min | Replies to `/status` `/today` `/stats` `/levels` `/help` |
| 🏁 **EOD Report** | Mon–Fri 11:00 PM | Today's P&L + closes trades + commits CSV |
| 🔬 **Weekly Backtest** | Sunday 8:00 PM | 30-day stats per strategy × pair |

---

## 📊 Data persistence (committed to repo)

| File | What |
|------|------|
| `data/trades.csv` | Every signal: entry, SL, TP, lot, status, result_R, result_$, exit |
| `data/backtest_signals.csv` | All signals from last weekly backtest |
| `data/backtest_report.md` | Readable weekly stats |

Open these in **Excel / Google Sheets / Numbers** anytime → full audit trail.

---

## 🎯 Pairs configured

| Pair | yfinance ticker | Notes |
|------|----------------|-------|
| XAUUSD | `GC=F` | Primary |
| GBPUSD | `GBPUSD=X` | London breakouts |
| EURUSD | `EURUSD=X` | Most liquid |
| NAS100 | `NQ=F` | NY momentum |

Edit `bot/src/config.py` → `PAIRS` list to add/remove (enabled flag per pair).

---

## 💬 Telegram commands (type in your group)

| Command | Returns |
|---------|---------|
| `/help` | List of commands |
| `/status` | Open trades + today's count |
| `/today` | Today's P&L summary |
| `/stats` | Lifetime win rate, total R, total $ |
| `/levels` | Current XAUUSD CPR + PDH/PDL |

Reply latency: 0–5 min (cron polling).

---

## 📂 Project structure

```
forex_trade_tv/
├── README.md                  ⭐ this
├── requirements.txt
│
├── docs/
│   ├── 01_GLOSSARY.md
│   ├── 02_MARKET_PREP_ROUTINE.md
│   ├── 03_FUNDAMENTAL_AND_MACRO_GUIDE.md
│   └── 04_MT5_AUTOEXECUTE.md
│
├── strategies/                 🎯 TradingView Pine (1-5)
│
├── bot/
│   ├── src/
│   │   ├── config.py           ← PAIRS, strategies, risk %, telegram creds
│   │   ├── data.py             ← yfinance + Twelve Data
│   │   ├── indicators.py       ← ATR/EMA/VWAP/CPR/FVG/swings
│   │   ├── strategies/         ← s1...s5
│   │   ├── trade_log.py        ← CSV log + outcome eval
│   │   ├── position_size.py    ← lot calc per pair
│   │   ├── news.py             ← ForexFactory XML
│   │   ├── formatters.py
│   │   └── telegram_notify.py
│   ├── run_signals.py
│   ├── run_morning_brief.py
│   ├── run_news_watcher.py
│   ├── run_eod_report.py
│   ├── run_backtest.py
│   └── run_commands.py
│
├── data/                       📊 trade history + backtest output
│
└── .github/workflows/
    ├── signals.yml
    ├── morning_brief.yml
    ├── news_watcher.yml
    ├── eod_report.yml
    ├── backtest.yml
    ├── commands.yml
    └── test_telegram.yml
```

---

## 🚀 Deploy

```bash
cd /Users/naveenkumarmadhesh/Documents/test_naveen/forex_trade_tv
git add .
git commit -m "Full automation: multi-pair, EOD CSV, backtest, commands"
git push
```

Then GitHub → **Actions** → enable any newly-added workflows.

**Test it now:** Actions → 🏁 EOD Report → Run workflow. Should send an empty summary to Telegram.

---

## ⚙️ Tuning

Everything in `bot/src/config.py`:

```python
account_size_usd = 10_000
risk_pct = 0.5

enable_strategies = [
    "s1_asian_breakout_cpr",
    "s2_pdh_pdl_cpr",
    "s3_smc_sweep_fvg",
    "s4_orb",
    "s5_vwap_bounce",
]

PAIRS = [
    PairConfig("XAUUSD",  "GC=F",     ..., enabled=True),
    PairConfig("GBPUSD",  "GBPUSD=X", ..., enabled=True),
    PairConfig("EURUSD",  "EURUSD=X", ..., enabled=True),
    PairConfig("NAS100",  "NQ=F",     ..., enabled=False),  # disable
]
```

---

## 🎓 90-day roadmap

| Phase | Weeks | Action |
|-------|-------|--------|
| Learn | 1–2 | Read all docs. Watch signals. Don't trade live. |
| Paper | 3–4 | Manually paper-trade every Telegram signal in MT5 demo |
| Validate | 5–6 | Review `data/trades.csv` + backtest weekly. Confirm edge. |
| Live half | 7–10 | Funded account @ 0.25% risk (half size) |
| Live full | 11–12 | After 50+ trades, scale to 0.5% |
| Auto | 13+ | See `docs/04_MT5_AUTOEXECUTE.md` — Windows VPS for full automation |

---

## ⚠️ Security

The Telegram bot token is **hardcoded** in `bot/src/config.py`. Keep this repo **private**.

If you ever push it public:
1. `@BotFather` → `/revoke`
2. Update `config.py` with new token
3. Push

---

## 🏆 You now have:
- ✅ 5 Pine Script strategies for TradingView
- ✅ Same 5 strategies in Python, running 24/5 automatically
- ✅ 4 pairs monitored in parallel
- ✅ Auto position sizing
- ✅ Auto trade logging to CSV
- ✅ Auto EOD P&L reports
- ✅ Weekly backtest
- ✅ Telegram commands
- ✅ Red news avoidance
- ✅ Macro morning brief
- ✅ Path to full MT5 auto-execution

**An institutional-grade trading system, fully free, on GitHub.** 💪
