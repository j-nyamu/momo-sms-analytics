import json
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import check_basic_auth

DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "database", "momo.db"
)

COLUMNS = [
    "transaction_type", "amount", "currency", "fee", "balance_after",
    "sender", "receiver", "timestamp", "financial_transaction_id",
    "status", "raw_body",
]


def run(sql, params=(), fetch=None):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        if fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        return cur
    finally:
        conn.close()


def get_transaction(tid):
    return run("SELECT * FROM transactions WHERE id = ?", (tid,), fetch="one")


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        payload = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def authorized(self):
        if check_basic_auth(self.headers.get("Authorization")):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error": "Unauthorized"}')
        return False

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            return body if isinstance(body, dict) else None
        except json.JSONDecodeError:
            return None

    def get_id(self):
        parts = self.path.split("?")[0].strip("/").split("/")
        if parts[0] != "transactions":
            return "invalid"
        return parts[1] if len(parts) > 1 else None

    def do_GET(self):
        if not self.authorized():
            return
        tid = self.get_id()
        if tid == "invalid":
            return self.send_json(404, {"error": "Not found"})
        if tid is None:
            rows = run("SELECT * FROM transactions ORDER BY id", fetch="all")
            return self.send_json(200, rows)
        t = get_transaction(tid)
        if t:
            self.send_json(200, t)
        else:
            self.send_json(404, {"error": "Transaction not found"})

    def do_POST(self):
        if not self.authorized():
            return
        if self.get_id() is not None:
            return self.send_json(404, {"error": "Not found"})
        body = self.read_body()
        if body is None:
            return self.send_json(400, {"error": "Invalid JSON"})
        if not body.get("transaction_type"):
            return self.send_json(400, {"error": "transaction_type is required"})
        values = [body.get(c) for c in COLUMNS]
        placeholders = ", ".join("?" for _ in COLUMNS)
        cur = run(
            f"INSERT INTO transactions ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            values,
        )
        self.send_json(201, get_transaction(cur.lastrowid))

    def do_PUT(self):
        if not self.authorized():
            return
        tid = self.get_id()
        if tid in (None, "invalid") or not get_transaction(tid):
            return self.send_json(404, {"error": "Transaction not found"})
        body = self.read_body()
        if body is None:
            return self.send_json(400, {"error": "Invalid JSON"})
        updates = {k: v for k, v in body.items() if k in COLUMNS}
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            run(
                f"UPDATE transactions SET {set_clause} WHERE id = ?",
                list(updates.values()) + [tid],
            )
        self.send_json(200, get_transaction(tid))

    def do_DELETE(self):
        if not self.authorized():
            return
        tid = self.get_id()
        if tid in (None, "invalid") or not get_transaction(tid):
            return self.send_json(404, {"error": "Transaction not found"})
        run("DELETE FROM transactions WHERE id = ?", (tid,))
        self.send_json(200, {"message": "Deleted", "id": int(tid)})


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), Handler)
    print("API running at http://localhost:8000/transactions")
    server.serve_forever()