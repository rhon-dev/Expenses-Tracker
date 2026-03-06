"""
Web Server — Flask REST API + serves the HTML frontend.
Reuses tracker.py and ai_analysis.py directly.
Run: python3 server.py
Then open: http://localhost:5000
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
import tracker
import ai_analysis

tracker.init_db()

HTML_FILE = Path(__file__).parent / "index.html"


def json_response(handler, data, status=200):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    return json.loads(handler.rfile.read(length)) if length else {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"  [{args[1]}] {args[0]}" % ())  # suppress default logging

    def log_message(self, fmt, *args):
        pass  # silent

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        # Serve HTML
        if path == "/" or path == "/index.html":
            if HTML_FILE.exists():
                content = HTML_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                json_response(self, {"error": "index.html not found"}, 404)
            return

        # API routes
        if path == "/api/expenses":
            qs = parse_qs(urlparse(self.path).query)
            category = qs.get("category", [None])[0]
            limit = int(qs.get("limit", [50])[0])
            expenses = tracker.get_expenses(category=category, limit=limit)
            json_response(self, expenses)

        elif path == "/api/summary":
            json_response(self, tracker.get_summary())

        elif path == "/api/personality":
            expenses = tracker.get_expenses(limit=200)
            key = tracker.classify_personality(expenses)
            if not key:
                json_response(self, {"error": "insufficient_data", "count": len(expenses)}, 422)
                return
            report = tracker.get_personality_report(key)
            ai = ai_analysis.get_ai_insight(expenses, report["title"])
            json_response(self, {
                "key": key,
                "report": report,
                "ai": ai,
                "expense_count": len(expenses),
            })

        elif path == "/api/categories":
            json_response(self, tracker.CATEGORIES)

        else:
            json_response(self, {"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/expenses":
            try:
                data = read_body(self)
                expense_id = tracker.add_expense(
                    data["description"],
                    float(data["amount"]),
                    data["category"],
                    data["date"],
                )
                json_response(self, {"id": expense_id, "ok": True}, 201)
            except (KeyError, ValueError) as e:
                json_response(self, {"error": str(e)}, 400)
        else:
            json_response(self, {"error": "not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        # DELETE /api/expenses/<id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "expenses":
            try:
                expense_id = int(parts[2])
                ok = tracker.delete_expense(expense_id)
                json_response(self, {"ok": ok}, 200 if ok else 404)
            except ValueError:
                json_response(self, {"error": "invalid id"}, 400)
        else:
            json_response(self, {"error": "not found"}, 404)


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  💸 Expense Tracker running at http://localhost:{PORT}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 Server stopped.\n")
