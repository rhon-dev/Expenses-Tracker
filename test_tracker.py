"""
Tests for tracker.py — no external test framework needed.
Run: python test_tracker.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Redirect DB to a temp file during tests
tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()

import tracker
tracker.DB_PATH = Path(tmp.name)
tracker.init_db()

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
passed = failed = 0


def test(name, condition):
    global passed, failed
    if condition:
        print(f"  {PASS}  {name}")
        passed += 1
    else:
        print(f"  {FAIL}  {name}")
        failed += 1


print("\n\033[1m  Running Expense Tracker Tests\033[0m\n")

# ── add_expense ───────────────────────────────────────────────────────────────
id1 = tracker.add_expense("Coffee", 4.5, "Food", "2024-01-01")
test("add_expense returns an int id", isinstance(id1, int) and id1 > 0)

id2 = tracker.add_expense("Uber", 12.0, "Transport", "2024-01-02")
id3 = tracker.add_expense("Spotify", 9.99, "Entertainment", "2024-01-03")

try:
    tracker.add_expense("Bad cat", 5.0, "INVALID", "2024-01-01")
    test("add_expense rejects invalid category", False)
except ValueError:
    test("add_expense rejects invalid category", True)

# ── get_expenses ──────────────────────────────────────────────────────────────
all_exp = tracker.get_expenses()
test("get_expenses returns all 3 records", len(all_exp) == 3)

food_exp = tracker.get_expenses(category="Food")
test("get_expenses filters by category", len(food_exp) == 1 and food_exp[0]["description"] == "Coffee")

# ── get_summary ───────────────────────────────────────────────────────────────
summary = tracker.get_summary()
test("get_summary total is correct", abs(summary["total"] - 26.49) < 0.01)
test("get_summary count is correct", summary["count"] == 3)
test("get_summary breakdown has Food", "Food" in summary["breakdown"])

# ── delete_expense ────────────────────────────────────────────────────────────
result = tracker.delete_expense(id1)
test("delete_expense returns True on success", result is True)
result_bad = tracker.delete_expense(99999)
test("delete_expense returns False for missing id", result_bad is False)
test("expense count is now 2 after delete", tracker.get_summary()["count"] == 2)

# ── classify_personality ──────────────────────────────────────────────────────
test("classify returns None for < 3 expenses", tracker.classify_personality([]) is None)
test("classify returns None for 2 expenses",
     tracker.classify_personality([{"amount": 10, "category": "Food"},
                                    {"amount": 5, "category": "Bills"}]) is None)

# Bills-heavy → strategic
strategic_expenses = [
    {"amount": 200, "category": "Bills"},
    {"amount": 180, "category": "Bills"},
    {"amount": 10,  "category": "Food"},
    {"amount": 5,   "category": "Other"},
]
test("classify bills-heavy as strategic", tracker.classify_personality(strategic_expenses) == "strategic")

# Entertainment-heavy → lifestyle
lifestyle_expenses = [
    {"amount": 80,  "category": "Entertainment"},
    {"amount": 60,  "category": "Food"},
    {"amount": 70,  "category": "Food"},
    {"amount": 20,  "category": "Transport"},
]
test("classify entertainment-heavy as lifestyle", tracker.classify_personality(lifestyle_expenses) == "lifestyle")

# Shopping-heavy + high variance → impulse
impulse_expenses = [
    {"amount": 2,   "category": "Shopping"},
    {"amount": 180, "category": "Shopping"},
    {"amount": 3,   "category": "Shopping"},
    {"amount": 220, "category": "Shopping"},
]
test("classify shopping with high variance as impulse", tracker.classify_personality(impulse_expenses) == "impulse")

# ── personality report ────────────────────────────────────────────────────────
report = tracker.get_personality_report("strategic")
test("get_personality_report has all keys", all(k in report for k in ("icon", "title", "description", "traits", "advice")))
test("get_personality_report advice is non-empty", len(report["advice"]) > 0)

# ── cleanup ───────────────────────────────────────────────────────────────────
os.unlink(tmp.name)

# ── results ───────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n  {'─'*40}")
print(f"  \033[1m{passed}/{total} passed\033[0m", end="")
if failed:
    print(f"  \033[91m{failed} failed\033[0m")
else:
    print("  \033[92m All tests passed ✓\033[0m")
print()
sys.exit(0 if failed == 0 else 1)
