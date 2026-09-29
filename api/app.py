import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import check_basic_auth

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "processed", "transactions.json",
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    transactions = json.load(f)

for i, t in enumerate(transactions, start=1):
    t.setdefault("id", i)


def find(tid):
    for t in transactions:
        if str(t["id"]) == str(tid):
            return t
    return None


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
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def get_id(self):
        parts = self.path.strip("/").split("/")
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
            return self.send_json(200, transactions)
        t = find(tid)
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
        body["id"] = max((t["id"] for t in transactions), default=0) + 1
        transactions.append(body)
        self.send_json(201, body)

    def do_PUT(self):
        if not self.authorized():
            return
        tid = self.get_id()
        t = find(tid) if tid not in (None, "invalid") else None
        if not t:
            return self.send_json(404, {"error": "Transaction not found"})
        body = self.read_body()
        if body is None:
            return self.send_json(400, {"error": "Invalid JSON"})
        body.pop("id", None)
        t.update(body)
        self.send_json(200, t)

    def do_DELETE(self):
        if not self.authorized():
            return
        tid = self.get_id()
        t = find(tid) if tid not in (None, "invalid") else None
        if not t:
            return self.send_json(404, {"error": "Transaction not found"})
        transactions.remove(t)
        self.send_json(200, {"message": "Deleted", "id": t["id"]})


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), Handler)
    print("API running at http://localhost:8000/transactions")
    server.serve_forever()