CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT NOT NULL,
    amount REAL,
    currency TEXT DEFAULT 'RWF',
    fee REAL DEFAULT 0,
    balance_after REAL,
    sender TEXT,
    receiver TEXT,
    timestamp TEXT,
    financial_transaction_id TEXT,
    status TEXT,
    raw_body TEXT
);

CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);