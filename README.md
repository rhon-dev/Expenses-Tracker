# 💸 Expense Tracker + Spending Personality Analyzer

A full-featured Python CLI app that tracks your expenses and uses AI to classify
your spending personality — built with **zero third-party dependencies**.

## Features

- **Add / View / Delete** expenses with category tagging
- **Visual breakdown** with ASCII progress bars in the terminal
- **4 spending personality types** classified from real spend logic:
  - 🧠 Strategic Saver
  - 🎉 Lifestyle Spender
  - ⚡ Impulse Buyer
  - 🛒 Deal Hunter
- **AI-powered insight** via Anthropic Claude API (optional)
- **SQLite** persistence — data survives restarts
- **Tested** — 14 unit tests, no test framework needed

## Project Structure

```
expense_tracker/
├── tracker.py        # Core logic: DB, CRUD, classification
├── cli.py            # Terminal UI (ANSI colors, menus)
├── ai_analysis.py    # Anthropic API integration
├── test_tracker.py   # Unit tests (stdlib only)
└── README.md
```

## Quickstart

```bash
# 1. Clone / enter the project
cd expense_tracker

# 2. (Optional) Set your Anthropic API key for AI insights
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run
python3 cli.py

# 4. Run tests
python3 test_tracker.py
```

No `pip install` required. Python 3.10+ only.

## Architecture Decisions

| Decision | Reason |
|---|---|
| SQLite over CSV/JSON | Concurrent-safe, queryable, industry-standard |
| stdlib only | Zero dependency hell, runs anywhere Python runs |
| Separated `tracker.py` from `cli.py` | Core logic is testable without a terminal |
| Graceful AI fallback | App works offline; AI is an enhancement, not a requirement |
| ANSI colors via raw codes | No `rich`/`colorama` needed |

## Personality Classification Logic

Classification uses spend ratios + coefficient of variation (CV):

```
Bills > 40% + Shopping < 20%    → Strategic Saver
Entertainment > 30% OR Food > 35% → Lifestyle Spender
CV > 1.0 AND Shopping > 20%     → Impulse Buyer
Shopping > 30%                   → Deal Hunter
```

CV = standard deviation / mean — measures how erratic spending is.
