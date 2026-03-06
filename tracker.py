"""
Expense Tracker — Core logic
Handles all DB operations, classification, and analysis.
"""

import sqlite3
import json
import statistics
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "expenses.db"

CATEGORIES = ["Food", "Transport", "Shopping", "Entertainment", "Health", "Bills", "Other"]

PERSONALITIES = {
    "strategic": {
        "icon": "🧠",
        "title": "Strategic Saver",
        "description": "You treat money like a chess game — every move is calculated.",
        "traits": ["High savings rate", "Consistent spending", "Low impulse purchases"],
        "advice": [
            "Consider index funds — your discipline is rare, use it.",
            "Automate 20% of income into a high-yield savings account.",
            "You're already winning. Keep a 'fun budget' so you don't burn out.",
        ],
    },
    "lifestyle": {
        "icon": "🎉",
        "title": "Lifestyle Spender",
        "description": "You invest in experiences and quality of life — life is for living.",
        "traits": ["High entertainment spend", "Regular dining out", "Social spending"],
        "advice": [
            "Track 'joy per dollar' — some luxuries matter more than others.",
            "Set a monthly lifestyle cap: 30% of income max.",
            "Negotiate subscriptions annually — save $200-500/yr easily.",
        ],
    },
    "impulse": {
        "icon": "⚡",
        "title": "Impulse Buyer",
        "description": "You feel the urge and act — spontaneity is both your strength and risk.",
        "traits": ["Unplanned purchases", "High shopping frequency", "Varied spend patterns"],
        "advice": [
            "Try the 48-hour rule: wait 2 days before any non-essential purchase.",
            "Delete saved payment methods from shopping apps.",
            "Set a 'guilt-free' impulse budget of $50/month — then stick to it.",
        ],
    },
    "hunter": {
        "icon": "🛒",
        "title": "Deal Hunter",
        "description": "You never pay full price. Finding a deal feels like winning.",
        "traits": ["Bulk purchases", "Discount-driven shopping", "Price comparison mindset"],
        "advice": [
            "Use a cash-back card for everyday purchases — you already optimize.",
            "Beware 'deal traps': buying things you don't need because they're cheap.",
            "Channel your skill into investment research — same mindset, bigger returns.",
        ],
    },
}


# ─── Database ────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount    REAL NOT NULL CHECK(amount > 0),
                category  TEXT NOT NULL,
                date      TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)


# ─── CRUD ────────────────────────────────────────────────────────────────────

def add_expense(description: str, amount: float, category: str, expense_date: str) -> int:
    if category not in CATEGORIES:
        raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)",
            (description.strip(), round(amount, 2), category, expense_date),
        )
        return cursor.lastrowid


def get_expenses(category: Optional[str] = None, limit: int = 50) -> list[dict]:
    query = "SELECT * FROM expenses"
    params = []
    if category:
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def delete_expense(expense_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0


def get_summary() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category").fetchall()
        total_row = conn.execute("SELECT COUNT(*) as count, SUM(amount) as total FROM expenses").fetchone()

    total = total_row["total"] or 0.0
    count = total_row["count"] or 0
    breakdown = {r["category"]: round(r["total"], 2) for r in rows}
    return {"total": round(total, 2), "count": count, "breakdown": breakdown}


# ─── Personality Classification ───────────────────────────────────────────────

def classify_personality(expenses: list[dict]) -> Optional[str]:
    """
    Rule-based classification using spend ratios and variance.
    Returns a personality key or None if insufficient data.
    """
    if len(expenses) < 3:
        return None

    total = sum(e["amount"] for e in expenses)
    if total == 0:
        return None

    def pct(cat):
        return sum(e["amount"] for e in expenses if e["category"] == cat) / total

    shopping_r     = pct("Shopping")
    entertainment_r = pct("Entertainment")
    food_r         = pct("Food")
    bills_r        = pct("Bills")

    amounts = [e["amount"] for e in expenses]
    avg = statistics.mean(amounts)
    variance = statistics.variance(amounts) if len(amounts) > 1 else 0
    cv = (variance ** 0.5) / avg if avg else 0  # coefficient of variation

    if bills_r > 0.40 and shopping_r < 0.20:
        return "strategic"
    if entertainment_r > 0.30 or food_r > 0.35:
        return "lifestyle"
    if cv > 1.0 and shopping_r > 0.20:
        return "impulse"
    if shopping_r > 0.30:
        return "hunter"
    if entertainment_r > 0.20:
        return "lifestyle"
    return "strategic"


def get_personality_report(key: str) -> dict:
    return PERSONALITIES.get(key, {})
