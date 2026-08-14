"""
XAUUSD Account Growth Projection Calculator
=============================================
Based on your trading parameters:
  - Starting balance  : $5,100
  - Lot size rule     : +0.01 lot for every $100 cumulative profit
  - Win rate          : 60% (6 wins out of 10 trades)
  - Trades per month  : ~20 (1 per trading day)
  - Max lot cap       : 0.20 (safety limit — change MAX_LOT below)

NOTE: Lot size is updated ONCE at the start of each month.
      Updating after every trade creates unrealistic hyper-compounding.
"""

# ─── USER PARAMETERS ──────────────────────────────────────────────────────────
STARTING_BALANCE = 5100    # Your current account balance ($)
STARTING_LOT     = 0.01   # Lot size you start with
LOT_STEP         = 0.01   # Lot increase per milestone
PROFIT_MILESTONE = 100    # Raise lot every $X cumulative profit
WIN_RATE         = 0.60   # 60% win rate
TRADES_PER_MONTH = 20     # ~1 trade per trading day
MAX_LOT          = 0.20   # Hard cap — never exceed this lot size
# ──────────────────────────────────────────────────────────────────────────────

# Profit / Loss per 0.01 lot (3 realistic scenarios)
SCENARIOS = {
    "Conservative": {
        "avg_win_per_unit" : 50,   # $50 win  per 0.01 lot
        "avg_loss_per_unit": 25,   # $25 loss per 0.01 lot
        "description"      : "Small wins $50, SL $25 per 0.01 lot",
    },
    "Moderate": {
        "avg_win_per_unit" : 100,  # $100 win  per 0.01 lot
        "avg_loss_per_unit": 20,   # $20  loss per 0.01 lot
        "description"      : "Normal day  $100 win, SL $20 per 0.01 lot",
    },
    "Optimistic": {
        "avg_win_per_unit" : 150,  # $150 win  per 0.01 lot (strong breakout)
        "avg_loss_per_unit": 15,   # $15  loss per 0.01 lot
        "description"      : "Strong move $150 win, SL $15 per 0.01 lot",
    },
}


def calc_lot(balance: float) -> float:
    """Lot size based on cumulative profit. Capped at MAX_LOT."""
    profit = max(0.0, balance - STARTING_BALANCE)
    steps  = int(profit // PROFIT_MILESTONE)
    lot    = STARTING_LOT + steps * LOT_STEP
    return round(min(lot, MAX_LOT), 2)


def simulate(months: int, avg_win: float, avg_loss: float) -> list[dict]:
    """
    Month-by-month simulation.
    Lot size is FIXED at the start of each month (realistic approach).
    Within the month trades alternate W-L-W-L... pattern (realistic ordering).
    """
    balance = float(STARTING_BALANCE)
    wins_m  = round(TRADES_PER_MONTH * WIN_RATE)
    loss_m  = TRADES_PER_MONTH - wins_m
    results = []

    for month in range(1, months + 1):
        start_bal = balance

        # Fix lot at month start
        lot  = calc_lot(balance)
        mult = round(lot / 0.01)

        # Build trade list: spread wins and losses evenly (W L W L ... W W)
        trades = []
        for i in range(TRADES_PER_MONTH):
            if i % round(1 / WIN_RATE) == 0 and len([x for x in trades if x]) < wins_m:
                trades.append(True)
            else:
                trades.append(False)
        # Pad remaining
        actual_wins = sum(trades)
        while actual_wins < wins_m:
            for i in range(len(trades)):
                if not trades[i]:
                    trades[i] = True
                    actual_wins += 1
                    break
        while actual_wins > wins_m:
            for i in range(len(trades)):
                if trades[i]:
                    trades[i] = False
                    actual_wins -= 1
                    break

        month_pnl = 0.0
        for is_win in trades:
            pnl        = (avg_win * mult) if is_win else -(avg_loss * mult)
            month_pnl += pnl

        balance += month_pnl
        total_profit = balance - STARTING_BALANCE

        results.append({
            "month"       : month,
            "start"       : round(start_bal, 2),
            "end"         : round(balance, 2),
            "lot"         : lot,
            "monthly_pnl" : round(month_pnl, 2),
            "total_profit": round(total_profit, 2),
            "pct_return"  : round(total_profit / STARTING_BALANCE * 100, 1),
        })

    return results


# ─── PRINT HELPERS ────────────────────────────────────────────────────────────

def print_header():
    w = TRADES_PER_MONTH
    print("\n" + "=" * 68)
    print("   XAUUSD ACCOUNT GROWTH PROJECTION — 3 MONTHS")
    print("=" * 68)
    print(f"   Starting Balance  : ${STARTING_BALANCE:,}")
    print(f"   Starting Lot      : {STARTING_LOT}")
    print(f"   Lot Rule          : +{LOT_STEP} lot per ${PROFIT_MILESTONE} cumulative profit")
    print(f"   Max Lot Cap       : {MAX_LOT}")
    print(f"   Win Rate          : {int(WIN_RATE*100)}%  "
          f"({round(w*WIN_RATE)} wins / {round(w*(1-WIN_RATE))} losses per {w} trades)")
    print(f"   Lot updated       : once at the start of each month")
    print("=" * 68)


def print_lot_schedule():
    print("\n" + "─" * 68)
    print("   LOT SIZE SCHEDULE")
    print("─" * 68)
    print(f"   {'Cum. Profit':>14}  {'Balance':>10}  {'Lot':>6}  {'1-win @$50':>11}  {'1-loss @$20':>12}")
    print(f"   {'─'*57}")
    step = 0
    while True:
        profit  = step * PROFIT_MILESTONE
        balance = STARTING_BALANCE + profit
        lot     = round(STARTING_LOT + step * LOT_STEP, 2)
        if lot > MAX_LOT:
            lot = MAX_LOT
        mult    = round(lot / 0.01)
        w50     = 50 * mult
        l20     = 20 * mult
        marker  = " ← YOU ARE HERE" if step == 0 else (" ← MAX LOT" if lot == MAX_LOT else "")
        print(f"   ${profit:>13,}  ${balance:>9,}  {lot:>6.2f}  ${w50:>10,}  ${l20:>11,}{marker}")
        step += 1
        if lot >= MAX_LOT:
            break
    print("─" * 68)


def print_per_trade():
    print("\n" + "─" * 68)
    print("   SINGLE TRADE P&L AT EACH LOT SIZE")
    print("─" * 68)
    print(f"   {'Lot':>6}  {'Win $50/u':>11}  {'Win $100/u':>12}  "
          f"{'SL $20/u':>10}  {'SL $35/u':>10}  {'Risk/Reward':>12}")
    print(f"   {'─'*60}")
    step = 0
    while True:
        lot  = round(STARTING_LOT + step * LOT_STEP, 2)
        if lot > MAX_LOT:
            lot = MAX_LOT
        mult = round(lot / 0.01)
        w50  = 50 * mult
        w100 = 100 * mult
        l20  = 20 * mult
        l35  = 35 * mult
        rr   = round(w50 / l20, 1)
        print(f"   {lot:>6.2f}  ${w50:>10,}  ${w100:>11,}  ${l20:>9,}  ${l35:>9,}  {rr:>11.1f}:1")
        step += 1
        if lot >= MAX_LOT:
            break
    print("─" * 68)


def print_scenario(name: str, cfg: dict):
    results = simulate(3, cfg["avg_win_per_unit"], cfg["avg_loss_per_unit"])
    print(f"\n{'─'*68}")
    print(f"   SCENARIO: {name.upper()}")
    print(f"   {cfg['description']}")
    print(f"{'─'*68}")
    print(f"   {'Mo':>3}  {'Start ($)':>11}  {'Lot':>6}  {'Month P&L ($)':>14}  "
          f"{'Balance ($)':>12}  {'Total Profit':>13}  {'Return':>7}")
    print(f"   {'─'*63}")
    for r in results:
        sign = "+" if r["monthly_pnl"] >= 0 else "-"
        print(f"   {r['month']:>3}  {r['start']:>11,.0f}  {r['lot']:>6.2f}  "
              f"  {sign}${abs(r['monthly_pnl']):>11,.0f}  "
              f"{r['end']:>12,.0f}  ${r['total_profit']:>12,.0f}  {r['pct_return']:>6.1f}%")
    final = results[-1]
    print(f"   {'─'*63}")
    print(f"   ► 3-Month Result : Balance ${final['end']:,.0f}  |  "
          f"Profit ${final['total_profit']:,.0f}  |  Return {final['pct_return']}%")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_header()
    print_lot_schedule()
    print_per_trade()

    for name, cfg in SCENARIOS.items():
        print_scenario(name, cfg)

    wins_m = round(TRADES_PER_MONTH * WIN_RATE)
    loss_m = TRADES_PER_MONTH - wins_m

    print("\n" + "=" * 68)
    print("   KEY FACTS & RISK RULES")
    print("=" * 68)
    print(f"   Lot size is FIXED for the whole month — updated at month start.")
    print(f"   You start Month 1 at lot 0.01 (need $100 profit to move up).")
    print(f"   Max lot {MAX_LOT} reached after ${round((MAX_LOT-STARTING_LOT)/LOT_STEP*PROFIT_MILESTONE):,}"
          f" cumulative profit (balance ${STARTING_BALANCE + round((MAX_LOT-STARTING_LOT)/LOT_STEP*PROFIT_MILESTONE):,}).")
    print()
    print(f"   Monthly math (Moderate scenario at any lot size X):")
    print(f"     Wins  : {wins_m} trades × $100/unit × lot_mult  = income")
    print(f"     Losses: {loss_m} trades × $20/unit  × lot_mult  = cost")
    print(f"     Net / 0.01 lot unit = ({wins_m}×100) - ({loss_m}×20)"
          f" = ${wins_m*100 - loss_m*20}/unit/month")
    print()
    print(f"   RISK RULES:")
    print(f"   ─ NEVER increase lot if in drawdown — wait for new equity high.")
    print(f"   ─ Risk per trade should stay under 1-2% of balance.")
    print(f"     At $5,100 → max SL per trade = ${round(5100*0.01)}-${round(5100*0.02)}")
    print(f"   ─ At 0.01 lot your SL of $10-$40 fits within 1% rule. ✓")
    print(f"   ─ At 0.10 lot your SL is $100-$400 — check balance before trading.")
    print(f"   ─ Keep lot capped at {MAX_LOT} until balance exceeds"
          f" ${STARTING_BALANCE + round((MAX_LOT-STARTING_LOT)/LOT_STEP*PROFIT_MILESTONE):,}.")
    print("=" * 68 + "\n")
