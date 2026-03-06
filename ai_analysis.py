"""
AI Analysis — calls Anthropic API for personalized spending insights.
Gracefully degrades if no API key is set.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional


def get_ai_insight(expenses: list[dict], personality_title: str) -> Optional[dict]:
    """
    Sends spending summary to Claude and returns structured insight.
    Returns None if API key missing or request fails.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    total = sum(e["amount"] for e in expenses)
    from collections import Counter
    cat_totals = Counter()
    for e in expenses:
        cat_totals[e["category"]] += e["amount"]

    breakdown = ", ".join(
        f"{cat}: {round((amt/total)*100)}%"
        for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])
    )

    prompt = f"""You are a sharp, direct financial coach. Analyze this spending data:
- Transactions: {len(expenses)}, Total: ${total:.2f}
- Category breakdown: {breakdown}
- Spending personality detected: {personality_title}

Give a 2-sentence personal insight about their habits, then 3 brutally honest but actionable tips.
Respond ONLY as JSON (no markdown): {{"insight": "...", "tips": ["...", "...", "..."]}}"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            text = "".join(b["text"] for b in data["content"] if b["type"] == "text")
            return json.loads(text.strip())
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None
