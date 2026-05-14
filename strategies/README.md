# 📈 TradingView Pine Script Strategies — Setup Guide

Five complete, funded-account-safe strategies for **XAUUSD M15**.

| # | File | Idea | When it fires | Difficulty |
|---|------|------|---------------|-----------|
| 1 | `01_asian_breakout_cpr.pine` | Asian range breakout + CPR | London open (12:30 IST) | ⭐ |
| 2 | `02_pdh_pdl_breakout_cpr.pine` | Previous-day High/Low + CPR | London+NY | ⭐ |
| 3 | `03_smc_sweep_fvg.pine` | **Smart Money: liquidity sweep + FVG retest** | London+NY | ⭐⭐⭐ |
| 4 | `04_opening_range_breakout.pine` | First-15min range break (ORB) | London open + 3h | ⭐ |
| 5 | `05_vwap_bounce.pine` | Pullback to VWAP in trend | London+NY | ⭐⭐ |

> All 5 are complementary — running 3–5 together = signals nearly every day.
>
> **Don't understand "FVG", "Liquidity sweep", "VWAP"?** → Read `../docs/01_GLOSSARY.md` first.

---

## 🚀 How to Copy-Paste into TradingView (step-by-step)

### Step 1 — Open Pine Editor
1. Go to **[tradingview.com](https://www.tradingview.com)** and log in
2. Open any chart → set symbol to **`OANDA:XAUUSD`** (or your broker) → timeframe **15m**
3. At the bottom of the chart click **"Pine Editor"** tab

### Step 2 — Paste Strategy 1
1. In Pine Editor click **"Open"** → **"New blank script"** (or just clear the default)
2. Open `strategies/01_asian_breakout_cpr.pine` in VS Code
3. **Cmd+A → Cmd+C** (select all + copy)
4. Click into Pine Editor → **Cmd+A → Cmd+V** (paste, replacing all)
5. Click **"Save"** → name it `Asian Breakout CPR`
6. Click **"Add to chart"** ✅

You'll now see:
- 🟡 Yellow line = Daily Pivot
- 🔵 Aqua lines = CPR (TC / BC)
- 🟢 Green line = Asian High  |  🔴 Red line = Asian Low
- 🔺 Triangles where the strategy enters

### Step 3 — Paste Strategy 2 (in a second chart tab)
Repeat Step 2 with `02_pdh_pdl_breakout_cpr.pine`. Open it on a **second chart tab** (same XAUUSD M15).

---

## 📊 Run Backtest

1. After adding the strategy → click **"Strategy Tester"** tab at the bottom
2. Look at:
   - **Net Profit** (should be positive)
   - **Profit Factor** (>1.5 = good, >2 = excellent)
   - **Max Drawdown** (must stay under your funded-account DD limit, e.g. 10%)
   - **Win Rate** (40–55% is normal for breakout systems)
   - **Total Trades** (need >50 for statistical validity)

3. Try date ranges: **last 1 year**, **last 2 years**, **last 6 months** → edge should be consistent

4. Tune inputs in **Settings (⚙️)** panel:
   - `Risk %` → 0.5 (start safe)
   - `Max CPR width %` → try 0.4, 0.6, 0.8
   - `Require EMA50` → toggle on/off
   - `TP2 R multiple` → try 1.5, 2, 2.5, 3

---

## 🔔 Set Up Alerts (Free TradingView plan works)

> The scripts emit alerts via `alert()` — TradingView wraps these in one master alert.

1. With strategy on chart → click **"Alert" (clock ⏰ icon)** at top right
2. **Condition:** select the strategy name (e.g., *Asian Breakout + CPR [Naveen]*)
3. **Alert name:** `XAUUSD Strat1`
4. **Message:** leave default (script already provides smart text)
5. **Notifications tab** → enable:
   - ✅ **Push (mobile app)** ← install TradingView app, get instant phone notifications
   - ✅ **Email**
   - ✅ **Webhook** → for Telegram/Discord (optional, see below)
6. **Expiration:** uncheck "Stop on close" → set to max (~2 months on free plan, then re-create)
7. Click **"Create"** ✅

Repeat for Strategy 2.

### 📱 Get alerts on phone
Install **TradingView app** → log in same account → push alerts come instantly, free.

### 💬 (Optional) Telegram alerts via webhook
- Create a Telegram bot via @BotFather → get token + chat_id
- Use a free relay like `IFTTT` or `pipedream.com` to receive TradingView webhook → forward to Telegram
- Paste relay URL into the **Webhook URL** field on the alert

---

## ⚠️ Free Plan Limits — Important

| Limit | Free | Essential ($15/mo) | Plus ($30/mo) |
|-------|------|---------------------|----------------|
| Active alerts | **1** ❌ | 20 | 100 |
| Server-side alerts | No | Yes | Yes |
| Multiple charts | 1 layout | 5 | 10 |

**If you can only afford free:**
- Run **Strategy 1** as the active alert (it's higher quality)
- Visually check Strategy 2 each day at 12:30 IST and 7 PM IST

**Recommended:** Upgrade to **Essential** (~₹1,200/mo) — you'll easily make this back from one trade.

---

## 🧪 What to do AFTER backtest looks good

1. **Forward-test on demo** for 2 weeks (don't trade real funded account yet)
2. Log every signal in a spreadsheet → compare to backtest
3. Only when forward-test ≈ backtest → go live on funded account at **0.25% risk** (half of normal)
4. After 30 trades live, scale to 0.5%

---

## 🆘 Troubleshooting

| Issue | Fix |
|-------|-----|
| "Script could not be saved" | Check for red error marks on left margin; usually a paste issue — re-copy whole file |
| Zero trades in backtest | Your data range may not cover any London sessions; extend chart history (scroll left) |
| Different results than mine | Different broker = different data; results will be **directionally** similar, not identical |
| Alert says "trigger only once" | That's fine for live — the script alert fires on each new signal anyway |
| No CPR lines visible | Switch to M15 (not D1); CPR uses prior-day data so needs intraday TF |

---

## 📂 Files in this folder

```
strategies/
├── 01_asian_breakout_cpr.pine        ← Strategy 1
├── 02_pdh_pdl_breakout_cpr.pine      ← Strategy 2 (similar, complementary)
├── 03_smc_sweep_fvg.pine             ← Strategy 3 (Smart Money Concepts)
├── 04_opening_range_breakout.pine    ← Strategy 4 (ORB classic)
├── 05_vwap_bounce.pine               ← Strategy 5 (VWAP pullback)
└── README.md                          ← this file
```

## 🧠 Which strategies to run together?

| Combo | Why |
|-------|-----|
| **1 + 4** | Easiest — both are breakouts, beginner friendly |
| **1 + 3 + 4** ⭐ | Recommended — covers breakouts, reversals, volatility |
| **3 + 5** | Advanced — Smart Money setups only |
| **All 5** | Max signals — need Essential plan for 5 alerts |

---

**Next step:** Paste Strategy 1 into TradingView → run backtest → reply back with the **Net Profit / Profit Factor / Max DD / Win Rate** numbers you see and I'll help you tune it 🎯
