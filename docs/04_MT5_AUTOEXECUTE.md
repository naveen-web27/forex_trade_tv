# 🤖 MT5 Auto-Execute — From Signals to Real Trades

> **Why this can't run on GitHub Actions:** The `MetaTrader5` Python package only works on Windows + needs a persistent MT5 terminal logged into your broker. GitHub Actions runners are stateless Linux. You need a small **Windows VPS**.

---

## 💰 Cost

| VPS Provider | Specs | Price |
|--------------|-------|-------|
| **ForexVPS.net** | 2GB / Win Server | ~$25/mo |
| **Contabo Windows** | 8GB / Win Server | ~$10/mo ⭐ |
| **Cheap-Windows-VPS** | Basic | ~$5/mo |
| **AWS / Azure free tier** | Free 12 months | $0 (then ~$10/mo) |

Recommend: **Contabo** — best value, low latency to broker servers in EU/US.

---

## 🏗️ Architecture

```
GitHub Actions (signals)
        │
        ▼
   Telegram group  ←──── you watch from phone
        │
        ▼ (optional auto-route)
   Windows VPS (24/7)
        │
        ├── MT5 terminal (logged into prop firm)
        └── Python bridge (executor.py)
              ↑
              └─ polls Telegram OR reads webhook
```

**Two ways the VPS gets signals:**
1. **Telegram polling** — VPS reads bot messages and parses
2. **Webhook** — GitHub Actions also POSTs to a small Flask app on VPS

---

## 🚀 Setup Checklist

### Step 1 — Get a Windows VPS
1. Order Contabo Windows VPS (or any Windows Server 2019+)
2. Connect via **Remote Desktop (RDP)** from your phone (Microsoft RDP app — free)

### Step 2 — Install MT5
1. Download MT5 from your **prop firm's portal** (FTMO/MFF/FundedNext)
2. Log into your funded account
3. Enable **Algo Trading** (Tools → Options → Expert Advisors → Allow algo trading ✅)

### Step 3 — Install Python on VPS
```cmd
:: Open PowerShell on VPS
winget install Python.Python.3.11
pip install MetaTrader5 python-telegram-bot pandas requests
```

### Step 4 — Create executor script
File: `executor.py` on VPS (this code lives on VPS, not GitHub):

```python
import MetaTrader5 as mt5
import re, requests, time, os

BOT_TOKEN = "<your token>"
CHAT_ID   = "-4929420131"
LOT_SCALE = 1.0  # multiply signal lot size by this

mt5.initialize()  # connects to running MT5 terminal

def parse(text):
    """Extract LONG/SHORT, entry, SL, TP2, lot from signal message."""
    if "S" not in text: return None
    m = {
        "side":  "buy" if "LONG" in text else "sell",
        "entry": float(re.search(r"Entry.*?(\d+\.?\d*)", text).group(1)),
        "sl":    float(re.search(r"SL.*?(\d+\.?\d*)",    text).group(1)),
        "tp2":   float(re.search(r"TP2.*?(\d+\.?\d*)",   text).group(1)),
        "lot":   float(re.search(r"Lot size.*?(\d+\.?\d*)", text).group(1)),
        "symbol": "XAUUSD" if "XAUUSD" in text else None,
    }
    return m if m["symbol"] else None

def place(o):
    req = {
        "action":    mt5.TRADE_ACTION_DEAL,
        "symbol":    o["symbol"],
        "volume":    o["lot"] * LOT_SCALE,
        "type":      mt5.ORDER_TYPE_BUY if o["side"]=="buy" else mt5.ORDER_TYPE_SELL,
        "price":     mt5.symbol_info_tick(o["symbol"]).ask if o["side"]=="buy"
                     else mt5.symbol_info_tick(o["symbol"]).bid,
        "sl":        o["sl"],
        "tp":        o["tp2"],
        "deviation": 20,
        "magic":     10042,
        "comment":   "auto-from-signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    r = mt5.order_send(req)
    print(r)
    return r

last_id = 0
while True:
    upd = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                       params={"offset": last_id+1}).json().get("result", [])
    for u in upd:
        last_id = u["update_id"]
        text = u.get("channel_post", {}).get("text") or u.get("message", {}).get("text", "")
        if "<b>S" in text and ("LONG" in text or "SHORT" in text):
            sig = parse(text)
            if sig:
                place(sig)
    time.sleep(15)
```

### Step 5 — Make it auto-start
1. Create `start.bat`:
   ```bat
   python C:\bot\executor.py
   ```
2. Windows Task Scheduler → trigger on boot → run `start.bat`
3. Restart VPS to test

---

## ⚠️ Critical Funded-Account Rules

Before enabling auto-execute, **disable for a week** and paper trade. Then check your prop firm's rules:

| Rule | Most prop firms |
|------|----------------|
| Auto-trading allowed? | Usually YES |
| Copy-trading allowed? | Usually NO (this is NOT copy trading — it's your own EA) |
| News trading? | Often restricted ±2 min around red news |
| Max lot size per trade? | Often capped (e.g. 5 lots on $100k) |
| Holding through weekends? | Often forbidden — script should close Friday 8 PM IST |

Add safety checks to `executor.py`:
- Skip if spread > 50 cents on XAUUSD
- Skip if Friday after 8 PM IST
- Skip if equity DD > 4% today (stops before breaching 5% rule)

---

## 🎯 My Strong Recommendation

**Phase 1 (now → 1 month):** Keep manual. Watch Telegram signals, enter trades by hand. Build trust in the system.

**Phase 2 (1–3 months):** After you're confident the signals are profitable, set up VPS + auto-execute on **demo account** first.

**Phase 3 (3+ months):** Auto-execute on funded account with **half size** for first 50 trades, then scale.

⚠️ Auto-execute without proven edge = fast way to blow a funded account. **Validate first.**

---

## 🆘 Alternatives if VPS too expensive

1. **3Commas / Pionex** — paid services that copy Telegram → broker (~$30/mo)
2. **Pickmytrade** — Telegram → MT4/MT5 service (~$15/mo)
3. **Manual on phone** — open MT5 mobile app, copy values from Telegram (free, takes 30s)

For starting out, **manual on phone is fine**. You only get a few signals per day.
