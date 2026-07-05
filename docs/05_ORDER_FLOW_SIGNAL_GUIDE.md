# Module K — Smart Money / Institutional Order Flow Guide

## What It Shows

The bottom-left table analyses **cumulative buy vs sell volume** across the last N completed 1-hour blocks (default: 4 hours, IST timezone).

Each row accumulates the previous rows, so by row 4 you see the full 4-hour picture. The key insight: **volume tells you what institutions are doing, price tells you what retail is seeing.** When they disagree, that's the trade.

---

## Signal Table

| Signal | Condition | What To Do |
|---|---|---|
| 🏦 **ACCUMULATION** | Price ↓ (red candles) BUT buy vol > sell vol | Wait for bullish confirmation → **BUY** ★★★ |
| 🏦 **DISTRIBUTION** | Price ↑ (green candles) BUT sell vol > buy vol | Wait for bearish confirmation → **SELL** ★★★ |
| 🚀 **BULLISH FLOW** | 3+ of N hours are buy-dominant, price trending up | Buy on any pullback. Momentum building. |
| 📉 **BEARISH FLOW** | 3+ of N hours are sell-dominant, price trending down | Sell on any relief rally. Momentum building. |
| ⚖️ **MIXED / WAIT** | Equal buy and sell hours, no institutional agreement | **Do NOT trade.** Wait for next signal. |

---

## Extra Signals To Remember

### ★★★ Best Setup: Accumulation/Distribution + Virgin CPR
Price approaches a Daily / Weekly / Monthly VCPR band **and** the order flow shows Accumulation or Distribution = **highest probability reversal trade** in the system.

---

### Hidden Bullish Divergence (Accumulation pattern)
- Chart looks bearish: lower lows, red candles
- BUT 3–4 of the last N hours are buy-dominant
- Smart money is **absorbing retail sell orders** before moving UP

**Entry:** First bullish pin bar or engulfing candle on 15m or 1H  
**Stop:** Below the absorption zone low  
**Target:** Nearest VCPR band or previous swing high

---

### Hidden Bearish Divergence (Distribution pattern)
- Chart looks bullish: higher highs, green candles
- BUT 3–4 of the last N hours are sell-dominant
- Smart money is **selling into retail buy orders** before moving DOWN

**Entry:** First bearish pin bar or engulfing candle on 15m or 1H  
**Stop:** Above the distribution zone high  
**Target:** Nearest VCPR band or previous swing low

---

### Flow Exhaustion (contra-trend fade)
- BULLISH FLOW showing 4/4 hours buy-dominant
- BUT price barely moved up
- Buyers are **running out of fuel** → expect pullback or reversal

Inverse: BEARISH FLOW 4/4 but price barely fell → sellers exhausted.

---

### Flow Acceleration (trend-continuation)
- Each row's cumulative buy% is **increasing** row by row (e.g., 51% → 54% → 57% → 61%)
- Momentum is accelerating
- **Ride the trend, do not fade it early**

---

## DO NOT TRADE When

- ⚖️ MIXED FLOW signal is showing
- Red-impact news event within ±30 minutes (ForexFactory calendar)
- The nearest VCPR band was already touched this session (band turned grey ✓)
- Fewer than 2 completed 1H blocks (session just opened — not enough data)
- RSI > 70 for buy setups or RSI < 30 for sell setups (price already extended)

---

## Combine With (Filter Stack)

| Filter | Rule |
|---|---|
| 🟣 Daily VCPR | 3–5 setups/week — medium strength |
| 🔵 Weekly VCPR | 1–2 setups/month — strong HTF magnet |
| 🟠 Monthly VCPR | 1–2/quarter — institutional level ⭐ |
| EMA 200 | Price > EMA200 → only take BUY setups. Price < EMA200 → only SELL setups. |
| RSI | Enter buys when RSI is between 35–60. Enter sells when RSI is between 40–65. Avoid extremes. |
| Trend Change (H) | If Module H shows ↑ TREND badge, favour buys. ↓ TREND → favour sells. |

---

## Reading the Table (Quick Reference)

```
╔══════════════════════════════════════════════════════╗
║ 🕐 Block (IST)  │ 🟢 Cum.Buy │ 🔴 Cum.Sell │ Bias  ║
╠═════════════════╪════════════╪═════════════╪═══════╣
║ 14:00 (↑1H)     │   12,400   │    8,200    │ 🐂 60% ║  ← last 1H only
║ 13:00 (↑2H)     │   24,800   │   19,100    │ 🐂 57% ║  ← last 2H cumulative
║ 12:00 (↑3H)     │   31,200   │   27,900    │ 🐂 53% ║  ← last 3H cumulative
║ 11:00 (↑4H)     │   38,500   │   37,100    │ 🐂 51% ║  ← last 4H cumulative
╠═════════════════╪════════════╪═════════════╪═══════╣
║ 4H VERDICT      │ 4/4 bull   │  51.2% buy  │ 🐂 Net ║
╠═════════════════╧════════════╧═════════════╧═══════╣
║ SIGNAL: ⚖️ MIXED — buy% declining each hour,        ║
║         momentum fading. Wait for clearer signal.   ║
╚══════════════════════════════════════════════════════╝
```

Even though 4/4 hours are buy-dominant, the buy% is **falling** each hour (60% → 57% → 53% → 51%). This is **Flow Exhaustion** — buyers slowing down. Do not chase a long.

Condition	Signal
Price ↓ but buyers dominant	🏦 ACCUMULATION — Institutions BUYING dips
Price ↑ but sellers dominant	🏦 DISTRIBUTION — Institutions SELLING rally
3-4/4 hours buy dominant	🚀 BULLISH FLOW — more BUY orders likely incoming
3-4/4 hours sell dominant	📉 BEARISH FLOW — more SELL orders likely incoming
Mixed	⚖️ Wait
---

## Module K vs Module J

| | Module J (bottom-right) | Module K (bottom-left) |
|---|---|---|
| Shows | Last 5 individual 1H blocks | Cumulative flow across N hours |
| Purpose | See what happened each hour | Detect institutional bias overall |
| Key signal | Individual hour dominance | Divergence between price and flow |
| Best use | Spot a single strong hour | Confirm institutional direction |
