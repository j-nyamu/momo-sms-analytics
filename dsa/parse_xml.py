"""
parse_xml.py

Reads the MoMo SMS backup (modified_sms_v2.xml) and converts every <sms>
record into a Python dictionary (a JSON-ready object).

The useful details (amount, sender, receiver, fee, balance...) are not
separate XML fields. They are written inside the free-text "body" of each
SMS, so we pull them out with regular expressions.

Usage from other code:
    from dsa.parse_xml import parse_sms_file
    transactions = parse_sms_file("data/modified_sms_v2.xml")

Usage from the command line (writes a JSON file you can inspect):
    python dsa/parse_xml.py
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The SMS phone clock is in Rwanda time (UTC+2). Used only when a message
# body has no timestamp of its own and we fall back to the "date" attribute.
LOCAL_TZ = timezone(timedelta(hours=2))

# Label used for the person who owns the phone (the account holder).
OWNER = "account owner"

# Each rule is (transaction_type, pattern). The FIRST rule that matches wins,
# so more specific patterns must come before general ones.
# Named groups: amount = the money value, party = the other person/business.
RULES = [
    ("incoming_money",
     re.compile(r"You have received (?P<amount>[\d,]+) RWF from (?P<party>.+?) \(")),
    ("airtime",
     re.compile(r"payment of (?P<amount>[\d,]+) RWF to (?P<party>Airtime)")),
    ("payment",
     re.compile(r"Your payment of (?P<amount>[\d,]+) RWF to (?P<party>.+?) has been completed")),
    ("transfer",
     re.compile(r"(?P<amount>[\d,]+) RWF transferred to (?P<party>.+?) \(")),
    ("bank_transfer",
     re.compile(r"You have transferred (?P<amount>[\d,]+) RWF to (?P<party>.+?) \(")),
    ("bank_deposit",
     re.compile(r"bank deposit of (?P<amount>[\d,]+) RWF")),
    ("merchant_payment",
     re.compile(r"A transaction of (?P<amount>[\d,]+) RWF by (?P<party>.+?)\s+on your MOMO")),
    ("withdrawal",
     re.compile(r"via agent: (?P<party>.+?) \(.*?withdrawn (?P<amount>[\d,]+) RWF")),
    ("failed_transaction",
     re.compile(r"transaction with amount (?P<amount>[\d,]+) RWF for (?P<party>.+?) with message.*failed")),
]

# Small helper patterns that work on any message type.
FEE_RE = re.compile(r"Fee was:?\s*(?P<v>[\d,]+)", re.IGNORECASE)
BALANCE_RE = re.compile(r"new balance\s*:?\s*(?P<v>[\d,]+) RWF", re.IGNORECASE)
TXID_RE = re.compile(r"(?:TxId:|Financial Transaction Id:)\s*(?P<v>\d+)")
TIME_RE = re.compile(r"at (?P<v>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
# Trailing merchant code or phone number stuck onto a name, e.g. "Jane Smith 12845"
TRAILING_CODE_RE = re.compile(r"\s*(\(\d+\)|\d+)$")


def to_int(text):
    """Turn a string like '1,000' into the integer 1000. Returns None if empty."""
    if not text:
        return None
    return int(text.replace(",", ""))


def find_number(regex, body):
    """Run a helper regex on the body and return its number, or None."""
    match = regex.search(body)
    return to_int(match.group("v")) if match else None


def get_timestamp(body, date_ms):
    """
    Prefer the time written inside the message. If there is none, convert the
    'date' attribute (milliseconds since 1970) to a readable time instead.
    """
    match = TIME_RE.search(body)
    if match:
        return match.group("v").replace(" ", "T")
    moment = datetime.fromtimestamp(int(date_ms) / 1000, tz=LOCAL_TZ)
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


def classify(body):
    """
    Work out what kind of SMS this is.
    Returns (type, amount, party). Unknown messages (OTP codes, promos, etc.)
    come back as ('other', None, None).
    """
    for tx_type, pattern in RULES:
        match = pattern.search(body)
        if match:
            groups = match.groupdict()
            party = groups.get("party")
            if party:
                # Remove a trailing code/phone number so we keep just the name
                party = TRAILING_CODE_RE.sub("", party).strip()
            return tx_type, to_int(groups.get("amount")), party
    return "other", None, None


def build_record(record_id, sms):
    """Convert one <sms> XML element into one dictionary."""
    body = sms.get("body", "")
    tx_type, amount, party = classify(body)

    # Money coming IN: the other person is the sender and the owner receives.
    # Everything else is money going OUT: the owner sends to the other party.
    if tx_type in ("incoming_money", "bank_deposit"):
        sender, receiver = party or "bank/agent", OWNER
    elif tx_type == "other":
        sender, receiver = None, None
    else:
        sender, receiver = OWNER, party

    fee = find_number(FEE_RE, body)
    return {
        "id": record_id,
        "transaction_type": tx_type,
        "amount": amount,
        "currency": "RWF" if amount is not None else None,
        "fee": fee if fee is not None else (0 if amount is not None else None),
        "balance_after": find_number(BALANCE_RE, body),
        "sender": sender,
        "receiver": receiver,
        "timestamp": get_timestamp(body, sms.get("date", "0")),
        "financial_transaction_id": (
            TXID_RE.search(body).group("v") if TXID_RE.search(body) else None
        ),
        "status": "failed" if tx_type == "failed_transaction" else "completed",
        "raw_body": body,
    }


def parse_sms_file(xml_path):
    """
    Parse the whole XML file and return a list of dictionaries.
    Each record gets a simple id (1, 2, 3...) based on its position in the file.
    """
    root = ET.parse(xml_path).getroot()
    return [build_record(i, sms) for i, sms in enumerate(root.findall("sms"), start=1)]


if __name__ == "__main__":
    # Default paths assume you run this from the project root folder.
    xml_file = Path("data/modified_sms_v2.xml")
    out_file = Path("data/processed/transactions.json")

    records = parse_sms_file(xml_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    # Quick summary so you can sanity-check the parse.
    print(f"Parsed {len(records)} records -> {out_file}")
    for tx_type, count in Counter(r["transaction_type"] for r in records).most_common():
        print(f"  {tx_type:20s} {count}")
    sys.exit(0)