"""Daily trading wisdom — rotating quotes for the morning brief.
Picks one based on day-of-year so it's consistent but varied."""
from __future__ import annotations

from datetime import datetime
import pytz

from .config import CFG


QUOTES = [
    # Patience
    ("🧘", "The market rewards the patient and punishes the greedy. Wait for YOUR setup."),
    ("🧘", "Don't chase the market. The next train always comes. Missing a trade ≠ losing money."),
    ("🧘", "Patience is a position. Sitting on hands when there's no setup IS the trade."),
    ("🧘", "If you have to force it, it's not there. Walk away."),
    ("🧘", "The trader who waits for A+ setups beats the one taking every B-grade signal."),

    # Discipline
    ("⚔️", "Plan the trade, trade the plan. No exceptions."),
    ("⚔️", "Your stop loss is sacred. Never widen it. Never remove it."),
    ("⚔️", "Two losses → stop trading for the day. Tomorrow always comes."),
    ("⚔️", "Discipline = doing what you said you'd do, even when you don't feel like it."),
    ("⚔️", "The market doesn't care about your bills. Trade size, not your mood."),

    # Risk management
    ("🛡️", "Survive first. Profit second. You can't trade tomorrow if you're broken today."),
    ("🛡️", "Never risk more than you can lose without flinching. 0.3-0.5% per trade. Period."),
    ("🛡️", "Position size protects you. Conviction blows accounts."),
    ("🛡️", "Cut losses early. Let winners run. That's the whole game."),
    ("🛡️", "Funded accounts die from ONE big loss, not many small ones. Stay small."),

    # Psychology
    ("🧠", "Revenge trading is the #1 account killer. If you feel angry, close MT5."),
    ("🧠", "FOMO is a thief. The trade you missed is gone. Focus on the next."),
    ("🧠", "Your worst enemy isn't the market. It's the trader staring back at you."),
    ("🧠", "Trade your edge, not your emotions. Edge is math. Emotions are noise."),
    ("🧠", "Confidence comes from data, not feelings. Trust the backtest."),

    # Long game
    ("🌱", "Compounding works only if you don't blow up. Slow is fast."),
    ("🌱", "Aim for consistency, not jackpots. 1R a day = 240R a year."),
    ("🌱", "Pros target ₹1 Cr in 2 years. Amateurs target it next month — and never reach it."),
    ("🌱", "Every losing trade taken with discipline is a step forward. Every winning trade taken without it is a step back."),
    ("🌱", "Your edge isn't the strategy. It's executing the same strategy 1000 times without deviating."),

    # Mark Douglas wisdom
    ("📖", "“Anything can happen.” Accept this and stop predicting. Just execute."),
    ("📖", "“You don't need to know what will happen to make money.” Trade probabilities."),
    ("📖", "“The market is always right.” Don't argue. Adapt or step aside."),

    # Truth bombs
    ("💎", "95% of traders blow accounts. The 5% follow rules they wrote when calm."),
    ("💎", "The market is a device for transferring money from the impatient to the patient."),
    ("💎", "Boring trading = profitable trading. Exciting trading = bleeding account."),
    ("💎", "You don't need to be right often. You need to lose small and win big."),
]


def quote_of_the_day() -> str:
    """Deterministic pick based on day-of-year so it changes daily but is reproducible."""
    now = datetime.now(pytz.timezone(CFG.timezone))
    idx = now.timetuple().tm_yday % len(QUOTES)
    emoji, text = QUOTES[idx]
    return f"{emoji} <i>{text}</i>"
