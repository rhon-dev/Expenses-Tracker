"""
CLI Interface — Beautiful terminal UI using only Python stdlib.
No third-party deps required.
"""

import sys
import os
from datetime import date

import tracker
import ai_analysis

# ─── ANSI Colors ─────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

BLACK  = "\033[30m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
PURPLE = "\033[95m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"

BG_DARK = "\033[48;5;236m"

CATEGORY_COLORS = {
    "Food":          YELLOW,
    "Transport":     CYAN,
    "Shopping":      PURPLE,
    "Entertainment": GREEN,
    "Health":        RED,
    "Bills":         BLUE,
    "Other":         WHITE,
}

CATEGORY_EMOJI = {
    "Food": "🍜", "Transport": "🚗", "Shopping": "🛍️",
    "Entertainment": "🎬", "Health": "💊", "Bills": "⚡", "Other": "📦",
}

PERSONALITY_COLORS = {
    "strategic": CYAN,
    "lifestyle":  "\033[38;5;213m",  # pink
    "impulse":    YELLOW,
    "hunter":     PURPLE,
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def c(text, *codes):
    return "".join(codes) + str(text) + RESET


def hr(char="─", width=52, color=DIM):
    print(c(char * width, color))


def center(text, width=52):
    print(text.center(width))


def bar(pct: float, width: int = 20, color: str = CYAN) -> str:
    filled = round(pct / 100 * width)
    return c("█" * filled, color) + c("░" * (width - filled), DIM)


def prompt(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {c('›', CYAN, BOLD)} {label}{c(hint, DIM)}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return val if val else default


def pause():
    try:
        input(c("\n  Press Enter to continue...", DIM))
    except (EOFError, KeyboardInterrupt):
        pass


# ─── Screens ──────────────────────────────────────────────────────────────────

def print_header():
    clear()
    print()
    print(c("  ╔══════════════════════════════════════════════════╗", DIM))
    print(c("  ║", DIM) + c("        💸  EXPENSE TRACKER  +  AI ANALYZER       ", BOLD, WHITE) + c("║", DIM))
    print(c("  ╚══════════════════════════════════════════════════╝", DIM))
    print()


def print_menu():
    print_header()
    summary = tracker.get_summary()
    total_str = "${:.2f}".format(summary["total"])
    count_str = "({} transactions)".format(summary["count"])
    print(f"  {c('Total Tracked:', DIM)}  {c(total_str, BOLD, GREEN)}  {c(count_str, DIM)}")
    print()
    hr()
    options = [
        ("1", "➕", "Add Expense"),
        ("2", "📋", "View Expenses"),
        ("3", "📊", "Spending Summary"),
        ("4", "🧠", "Personality Analysis"),
        ("5", "🗑️ ", "Delete Expense"),
        ("0", "👋", "Exit"),
    ]
    for key, icon, label in options:
        print(f"  {c(f'[{key}]', BOLD, CYAN)}  {icon}  {label}")
    hr()
    print()


def screen_add():
    print_header()
    print(c("  ADD NEW EXPENSE\n", BOLD))

    desc = prompt("Description")
    if not desc:
        print(c("  ✗ Description required.", RED))
        pause()
        return

    amount_str = prompt("Amount ($)")
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print(c("  ✗ Invalid amount.", RED))
        pause()
        return

    print(f"\n  {c('Categories:', DIM)}")
    for i, cat in enumerate(tracker.CATEGORIES, 1):
        color = CATEGORY_COLORS.get(cat, WHITE)
        print(f"    {c(f'[{i}]', BOLD, CYAN)}  {CATEGORY_EMOJI[cat]}  {c(cat, color)}")

    cat_input = prompt("\n  Pick category", "1")
    try:
        cat_idx = int(cat_input) - 1
        category = tracker.CATEGORIES[cat_idx]
    except (ValueError, IndexError):
        print(c("  ✗ Invalid choice.", RED))
        pause()
        return

    today = date.today().isoformat()
    expense_date = prompt("Date (YYYY-MM-DD)", today)

    try:
        expense_id = tracker.add_expense(desc, amount, category, expense_date)
        print(f"\n  {c('✓', GREEN, BOLD)} Saved #{expense_id}: {c(desc, WHITE)} — {c(f'${amount:.2f}', GREEN)}")
    except Exception as e:
        print(c(f"  ✗ Error: {e}", RED))
    pause()


def screen_list():
    print_header()
    print(c("  RECENT EXPENSES\n", BOLD))

    print(f"  Filter by category? {c('(leave blank for all)', DIM)}")
    for i, cat in enumerate(tracker.CATEGORIES, 1):
        print(f"    {c(f'[{i}]', BOLD, CYAN)}  {CATEGORY_EMOJI[cat]}  {cat}")
    cat_input = prompt("\n  Category number", "")

    category = None
    if cat_input.isdigit():
        idx = int(cat_input) - 1
        if 0 <= idx < len(tracker.CATEGORIES):
            category = tracker.CATEGORIES[idx]

    expenses = tracker.get_expenses(category=category, limit=20)

    if not expenses:
        print(c("\n  No expenses found.", DIM))
        pause()
        return

    print()
    hr()
    print(f"  {c('ID', DIM):<12} {c('Date', DIM):<14} {c('Category', DIM):<16} {c('Amount', DIM):<12} {c('Description', DIM)}")
    hr()

    for e in expenses:
        color = CATEGORY_COLORS.get(e["category"], WHITE)
        emoji = CATEGORY_EMOJI.get(e["category"], "")
        eid = "#{:d}".format(e["id"])
        amt = "${:.2f}".format(e["amount"])
        print(
            f"  {c(eid, DIM):<12}"
            f" {e['date']:<14}"
            f" {c(emoji + ' ' + e['category'], color):<16}"
            f" {c(amt, GREEN):<12}"
            f" {e['description'][:30]}"
        )
    hr()
    pause()


def screen_summary():
    print_header()
    print(c("  SPENDING SUMMARY\n", BOLD))

    summary = tracker.get_summary()
    total = summary["total"]
    breakdown = summary["breakdown"]

    if not breakdown:
        print(c("  No data yet. Add some expenses first.", DIM))
        pause()
        return

    print(f"  {c('Total:', DIM)} {c(f'${total:.2f}', BOLD, GREEN)}  |  {c(str(summary['count']) + ' transactions', DIM)}\n")
    hr()

    sorted_cats = sorted(breakdown.items(), key=lambda x: -x[1])
    for cat, amt in sorted_cats:
        pct = (amt / total * 100) if total else 0
        color = CATEGORY_COLORS.get(cat, WHITE)
        emoji = CATEGORY_EMOJI.get(cat, "")
        label = f"{emoji} {cat}"
        print(f"  {c(label, color):<20}  {bar(pct, 18, color)}  {c(f'{pct:5.1f}%', DIM)}  {c(f'${amt:.2f}', BOLD)}")
    hr()
    pause()


def screen_personality():
    print_header()
    print(c("  SPENDING PERSONALITY ANALYSIS\n", BOLD))

    expenses = tracker.get_expenses(limit=200)

    if len(expenses) < 3:
        print(c(f"  Need at least 3 expenses to analyze. You have {len(expenses)}.", YELLOW))
        pause()
        return

    print(c(f"  Analyzing {len(expenses)} transactions...\n", DIM))

    key = tracker.classify_personality(expenses)
    if not key:
        print(c("  Could not classify. Add more varied expenses.", DIM))
        pause()
        return

    p = tracker.get_personality_report(key)
    p_color = PERSONALITY_COLORS.get(key, CYAN)

    # Personality card
    print(c("  ┌─────────────────────────────────────────────────┐", p_color))
    icon_title = f"  {p['icon']}  {p['title']}"
    print(c(f"  │{icon_title:<51}│", p_color, BOLD))
    print(c("  └─────────────────────────────────────────────────┘", p_color))
    print()
    print(f"  {c(p['description'], WHITE)}")
    print()

    print(c("  TRAITS", DIM, BOLD))
    for trait in p["traits"]:
        print(f"   {c('·', p_color)} {trait}")
    print()

    # AI insight
    print(c("  Fetching AI insight...", DIM), end="", flush=True)
    ai = ai_analysis.get_ai_insight(expenses, p["title"])
    print("\r" + " " * 30 + "\r", end="")

    if ai:
        print(c("  ✦ AI INSIGHT", CYAN, BOLD))
        print(f"  {c('\"' + ai['insight'] + '\"', WHITE)}")
        print()
        print(c("  ACTION PLAN", CYAN, BOLD))
        tips = ai.get("tips", p["advice"])
    else:
        print(c("  ACTION PLAN", CYAN, BOLD))
        tips = p["advice"]

    for i, tip in enumerate(tips, 1):
        print(f"\n  {c(str(i) + '.', p_color, BOLD)} {tip}")

    print()
    hr()
    pause()


def screen_delete():
    print_header()
    print(c("  DELETE EXPENSE\n", BOLD))

    expenses = tracker.get_expenses(limit=10)
    if not expenses:
        print(c("  No expenses found.", DIM))
        pause()
        return

    for e in expenses:
        color = CATEGORY_COLORS.get(e["category"], WHITE)
        eid2 = "#{:d}".format(e["id"])
        amt2 = "${:.2f}".format(e["amount"])
        print(f"  {c(eid2, BOLD, CYAN)}  {e['date']}  {c(e['category'], color):<14}  "
              f"{c(amt2, GREEN)}  {e['description'][:28]}")

    print()
    id_str = prompt("Enter ID to delete (or 0 to cancel)", "0")
    if id_str == "0":
        return

    try:
        expense_id = int(id_str)
    except ValueError:
        print(c("  ✗ Invalid ID.", RED))
        pause()
        return

    confirm = prompt(f"Delete #{expense_id}? (y/n)", "n")
    if confirm.lower() == "y":
        if tracker.delete_expense(expense_id):
            print(c(f"\n  ✓ Expense #{expense_id} deleted.", GREEN))
        else:
            print(c(f"\n  ✗ ID #{expense_id} not found.", RED))
    else:
        print(c("  Cancelled.", DIM))
    pause()


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    tracker.init_db()

    SCREENS = {
        "1": screen_add,
        "2": screen_list,
        "3": screen_summary,
        "4": screen_personality,
        "5": screen_delete,
    }

    while True:
        print_menu()
        try:
            choice = input(c("  Your choice: ", CYAN, BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            choice = "0"

        if choice == "0":
            clear()
            print(c("\n  👋  See you next time!\n", CYAN))
            sys.exit(0)
        elif choice in SCREENS:
            SCREENS[choice]()
        else:
            print(c("  Invalid choice.", RED))


if __name__ == "__main__":
    main()
