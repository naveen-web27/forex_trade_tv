# 🤖 Forex Signal Bot — GitHub Actions Automation

Fully automated trading signal scanner that runs on **GitHub Actions** (free tier) and sends alerts to **Telegram**.

## What it does

| Workflow | Schedule | What it sends |
|----------|----------|---------------|
| **Signal Scanner** | Every 15 min, Mon–Fri, 12:00–22:30 IST | XAUUSD signals from 5 strategies |
| **Morning Brief** | 11:30 AM IST daily | Today's red news + macro bias + key levels |
| **News Watcher** | Every hour | Upcoming red news warning (30 min before) |

All goes to your Telegram group.

---

## 🚀 Setup (one-time, ~10 minutes)

### Step 1 — Revoke leaked bot token & create new
1. Open Telegram → search **@BotFather**
2. Send `/revoke` → pick your bot → confirm
3. `/token` → pick your bot → get **new token**
4. **Don't paste it anywhere yet** — keep the chat open

### Step 2 — Push this repo to GitHub
```bash
cd /Users/naveenkumarmadhesh/Documents/test_naveen/forex_trade_tv
git add .
git commit -m "Add GitHub Actions signal bot"
git push origin main
```

### Step 3 — Add GitHub Secrets
1. Go to your repo on GitHub
2. **Settings → Secrets and variables → Actions → New repository secret**
3. Add these two secrets:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | the new token from BotFather |
| `TELEGRAM_CHAT_ID` | `-4929420131` (your group) |

### Step 4 — Enable Actions
1. Repo → **Actions** tab → enable workflows
2. Click each workflow → **"Enable workflow"**
3. Click **"Run workflow"** manually first time to test

### Step 5 — Verify
Within 1 minute you should see a message in your Telegram group from the bot.

---

## 📂 Project structure

```
.github/workflows/
├── signals.yml          ← Runs strategies every 15 min (market hours)
├── morning_brief.yml    ← Daily 11:30 AM IST market prep summary
└── news_watcher.yml     ← Hourly news warning

src/
├── config.py            ← Settings (pairs, timeframes, risk)
├── data.py              ← Fetch XAUUSD OHLC data (yfinance + Twelve Data fallback)
├── indicators.py        ← ATR, EMA, VWAP, RSI, CPR, swings, FVG
├── telegram_notify.py   ← Send formatted messages
├── news.py              ← Fetch ForexFactory news XML
├── macro.py             ← Fetch DXY, US10Y, GLD via yfinance
├── strategies/
│   ├── s1_asian_breakout_cpr.py
│   ├── s2_pdh_pdl_cpr.py
│   ├── s3_smc_sweep_fvg.py
│   ├── s4_orb.py
│   └── s5_vwap_bounce.py
├── run_signals.py       ← Entry point: scan all 5 strategies
├── run_morning_brief.py ← Entry point: daily summary
└── run_news_watcher.py  ← Entry point: news alerts

requirements.txt
```

---

## 🔔 What you'll receive

### Signal alert (example)
```
🟢 STRAT3 SMC LONG  XAUUSD
─────────────────────
Entry:  2,048.20
SL:     2,043.50   (-$4.70  | 0.5% acct)
TP1:    2,052.90   (1R)
TP2:    2,057.60   (2R)
─────────────────────
Reason: Bullish liquidity sweep + FVG retest
Time:   14:15 IST
Bias:   DXY ↓, no red news next 4h ✅
```

### Morning brief
```
🌅 GOOD MORNING — 14 May 2026
─────────────────────────────
📰 RED NEWS TODAY:
  🔴 18:00 IST | USD CPI YoY
  🔴 23:30 IST | FOMC Minutes
  ⚠️ Avoid trades 30 min around these

📊 MACRO SNAPSHOT:
  DXY:    104.32  (+0.15%, uptrend)
  US10Y:  4.41%   (+2bp)
  Gold:   2,046   (-0.3%)

🎯 KEY LEVELS XAUUSD:
  PDH:    2,058.40
  PDL:    2,041.20
  Pivot:  2,048.80
  TC/BC:  2,051.20 / 2,045.80

🧭 BIAS: Short bias (DXY strong)
```

---

## ⚙️ Customize

Edit `src/config.py`:
- Change pair (default `GC=F` = Gold futures, most liquid free data)
- Change timeframe
- Enable/disable strategies
- Change risk %

---

## ❓ FAQ

**Q: Will GitHub Actions actually run every 15 min?**
A: Cron jobs run within ±5–10 min of scheduled time on free tier. Good enough for M15 signals.

**Q: Free tier limits?**
A: 2,000 minutes/month. Each run takes ~30 sec. We schedule ~40 runs/day = ~10 min/day = ~300 min/month. Well within limits ✅

**Q: What if a strategy fires twice for same signal?**
A: We use a `state/` JSON file committed back to repo to prevent duplicates.

**Q: Can I add more pairs?**
A: Yes — add to `PAIRS` list in `config.py`.

---

📚 Read `../docs/01_GLOSSARY.md` if any term is unclear.
