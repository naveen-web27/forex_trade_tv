# 🚀 Forex Trading System — Complete Knowledge Base + Pine Scripts

Personal trading workspace for **XAUUSD funded account growth → ₹1 Cr**.

---

## 📂 Folder Structure

```
forex_trade_tv/
├── docs/
│   ├── 01_GLOSSARY.md                    ← All trading terms explained
│   ├── 02_MARKET_PREP_ROUTINE.md         ← Daily morning routine
│   └── 03_FUNDAMENTAL_AND_MACRO_GUIDE.md ← Economics + news + data sources
│
├── strategies/                            🎯 TradingView Pine Scripts
│   ├── 01_asian_breakout_cpr.pine
│   ├── 02_pdh_pdl_breakout_cpr.pine
│   ├── 03_smc_sweep_fvg.pine
│   ├── 04_opening_range_breakout.pine
│   ├── 05_vwap_bounce.pine
│   └── README.md
│
├── bot/                                   🤖 Python automation → Telegram
│   ├── README.md                         ← Setup guide (READ THIS for bot)
│   ├── src/                              ← Strategies, indicators, data, news
│   ├── run_signals.py                    ← Every 15 min: scan & alert
│   ├── run_morning_brief.py              ← 11:30 AM IST daily brief
│   └── run_news_watcher.py               ← Hourly red-news warnings
│
├── .github/workflows/                     ⚙️  GitHub Actions automation
│   ├── signals.yml
│   ├── morning_brief.yml
│   ├── news_watcher.yml
│   └── test_telegram.yml                 ← Manual trigger to test bot
│
├── requirements.txt
└── README.md  (this file)
```

---

## 🎯 Quick Start (3 actions today)

### 1. Read in this order (90 minutes)
1. 📖 `docs/01_GLOSSARY.md` — get every term clear
2. 🌅 `docs/02_MARKET_PREP_ROUTINE.md` — daily checklist
3. 🌍 `docs/03_FUNDAMENTAL_AND_MACRO_GUIDE.md` — news & data

### 2. Set up TradingView (15 minutes)
1. Open `strategies/README.md` — follow copy-paste guide
2. Paste **Strategy 1, 3, 4** into Pine Editor (start with these 3)
3. Create alerts on each → enable phone push notifications

### 3. Bookmark these URLs
- [ForexFactory Calendar](https://www.forexfactory.com/calendar) (set IST timezone)
- [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)
- [TradingEconomics](https://tradingeconomics.com)
- [Kitco News](https://www.kitco.com/news/) (gold specific)

---

## 🧠 The 5 Strategies

| # | Name | When it fires | Difficulty | Best for |
|---|------|---------------|------------|----------|
| 1 | Asian Breakout + CPR | London open breakout | ⭐ | Trending days |
| 2 | PDH/PDL + CPR | Prior-day level break | ⭐ | Continuation |
| 3 | SMC Sweep + FVG | Liquidity grab + imbalance | ⭐⭐⭐ | Reversals |
| 4 | Opening Range Breakout | First 15min break | ⭐ | Volatility expansion |
| 5 | VWAP Bounce | Pullback in trend | ⭐⭐ | Trending days |

**Recommended combo:** Run **1 + 3 + 4** simultaneously → covers breakouts, reversals, and volatility plays.

---

## 📊 The Path to ₹1 Cr (realistic plan)

| Phase | Months | Action | Target |
|-------|--------|--------|--------|
| **Learn** | 1–2 | Read all docs, paper trade Pine scripts | Understand every signal |
| **Backtest** | 1 | TradingView Strategy Tester on all 5 | Find best 2–3 strategies |
| **Demo** | 2 | Forward-test on demo MT5 | Match backtest results |
| **Funded #1** | 3 | Pass first challenge | $10k account |
| **Scale** | 6 | Multiple funded accounts (FTMO, MFF, FN) | $100k+ combined |
| **Cash out** | 12–24 | Consistent 6–10%/month payouts | ₹1 Cr cumulative |

**Key rules:**
- Risk ≤ 0.5% per trade
- Max 2 trades/day
- No trading 30 min around red news
- Stop trading after 2 losses in a day
- Journal every trade

---

## ⚠️ Funded Account Survival Rules

1. **Daily DD limit** → if approaching, STOP trading for the day
2. **Max DD limit** → if approaching, withdraw + restart fresh
3. **Consistency rule** (FTMO etc.) → don't have one giant winning day vs many small
4. **News rule** → many prop firms ban trading 5 min around red news
5. **Weekend rule** → close all positions Friday 8 PM IST

---

## 🛠️ Tools Stack

| Need | Tool |
|------|------|
| Charts + backtest | TradingView (free → Essential ₹1,200/mo) |
| News | ForexFactory + Investing.com mobile app |
| Live trading | MT5 (from your prop firm) |
| Journal | Notion / Excel / Edgewonk |
| Macro data | TradingEconomics + FRED |
| VPS (later) | Contabo / ForexVPS ~₹500–1500/mo |

---

## 📈 Next Levels (when you're ready)

- **Phase 2:** Python backtester (more precise than TV Strategy Tester)
- **Phase 3:** MT5 Expert Advisor (full automation)
- **Phase 4:** Multi-pair portfolio (XAUUSD + GBPUSD + NAS100)
- **Phase 5:** Custom Python + ML signals

Just ask when you're ready and I'll build them.

---

## ❤️ Final Wisdom

> **"Amateurs focus on rewards. Professionals focus on risk."**
>
> Trading is 80% psychology, 15% risk management, 5% strategy.
> All 5 of your strategies are good. **Your discipline is what wins.**

📝 Journal every day. Review every week. Improve every month.

**You got this, Naveen.** 🚀
