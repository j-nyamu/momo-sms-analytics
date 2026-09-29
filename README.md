# MoMo SMS Analytics

## Team 
- Members: Mungiiria Junior Nyamu, Ahmed Ousmane

## Project Description
Processes MoMo (Mobile Money) SMS data from XML, cleans and categorizes
transactions, stores them in a relational database (MySQL/MariaDB), and
exposes a frontend dashboard for analysis and visualization.

## Architecture
High-level system architecture diagram: `docs/architecture_diagram.png`
(Miro link: TBD)

## Database Design

### Entity Relationship Diagram
See `docs/ERD.png`.

The schema has five entities:

- **Users** — people/entities that send or receive money (customers, merchants, agents, system accounts)
- **Transaction_Categories** — lookup table of transaction types (Incoming Money, Payment, Bank Deposit, Transfer, Airtime Purchase, Data Bundle Purchase)
- **Transactions** — one row per parsed MoMo SMS transaction; the core fact table
- **Transaction_Participants** — junction table resolving the many-to-many relationship between `Transactions` and `Users` (each transaction has a sender and a receiver; each user appears across many transactions), tagged with a `role`
- **System_Logs** — ETL processing/audit trail, including entries for SMS that failed to parse into a transaction

### Design Rationale
The schema separates raw SMS ingestion from structured transaction data to
preserve auditability while enabling efficient querying. `Transactions` is
the central fact table, holding numeric and temporal data needed for
analytics (amount, fee, balance, datetime), with `raw_body` retained for
traceability back to the source SMS.

`Users` is deliberately generic rather than split into Senders/Receivers,
since the same person can appear as both across different transactions —
normalizing them into one table avoids duplicate records and enables
per-user transaction history. The relationship between `Transactions` and
`Users` is naturally many-to-many: one transaction involves two users
(sender, receiver), and one user participates in many transactions. This
is resolved with the `Transaction_Participants` junction table, which also
carries the `role` attribute distinguishing sender from receiver.

`Transaction_Categories` is separated out rather than using a plain string
column, since the ETL categorization step already classifies transactions
into a fixed set of types, and a lookup table keeps this consistent and
query-efficient.

`System_Logs` supports the ETL pipeline's error-handling path, capturing
SMS that failed to parse alongside successfully processed transaction
logs, without forcing every SMS to become a `Transactions` row.

### SQL Setup
Full schema (DDL + sample data) is in `database/database_setup.sql`. Each
team member should install MySQL locally and run the script against their
own instance — no shared credentials needed, the script builds the full
database from scratch.

**Windows (PowerShell):**
```
Get-Content database\database_setup.sql | mysql -u root -p
```
If `mysql` isn't recognized, PowerShell doesn't have it on PATH — either
add `C:\Program Files\MySQL\MySQL Server 8.0\bin` to your PATH environment
variable, or call it directly:
```
Get-Content database\database_setup.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

**macOS/Linux:**
```
mysql -u root -p < database/database_setup.sql
```

You'll be prompted for the root password you set during MySQL install.
Verify it worked with:
```
mysql -u root -p -e "USE momo_sms_analytics; SHOW TABLES;"
```
You should see all 5 tables: `users`, `transaction_categories`,
`transactions`, `transaction_participants`, `system_logs`.

### JSON Data Modeling
`examples/json_schemas.json` contains a flat JSON example for each entity,
one fully nested `complete_transaction_example` (a transaction with its
sender, receiver, category, and logs embedded — the shape an API response
like `GET /transactions/1` would return), and a `sql_to_json_mapping`
section documenting how each table maps into the nested JSON structure.

## Scrum Board
Link: https://github.com/users/j-nyamu/projects/4

## Setup & Run
1. Run `database/database_setup.sql` against a local MySQL/MariaDB instance (see SQL Setup above)
2. Frontend and ETL setup instructions: TBD (added as those pieces are built)

---

# MoMo SMS Transactions API

A REST API built with plain Python (`http.server`) that serves mobile money SMS transactions parsed from XML. It supports full CRUD, Basic Authentication, and includes a DSA comparison of linear search vs dictionary lookup.

## Project structure

    api/           REST API (app.py) and Basic Auth (auth.py)
    data/          Source XML and processed transactions.json
    database/      SQLite schema, load script and momo.db
    dsa/           Linear search vs dictionary lookup comparison
    docs/          API documentation (api_docs.md)
    screenshots/   Test evidence (curl/Postman)

## Requirements

- Python 3.12 or newer
- No external packages needed (standard library only)

## Setup

1. Clone the repository:

       git clone https://github.com/j-nyamu/momo-sms-analytics.git
       cd momo-sms-analytics

2. Parse the XML into JSON (replace with your parser's path):

       python <path/to/your/parser.py>

   This creates `data/processed/transactions.json`.

3. Load the data into SQLite:

       python database/load_db.py

4. Start the API:

       python api/app.py

   The server runs at `http://localhost:8000`.

## Authentication

All endpoints require Basic Auth.

- Username: `admin`
- Password: `password123`

Invalid or missing credentials return `401 Unauthorized`.

## Quick test

    curl.exe -u admin:password123 http://localhost:8000/transactions/1

(On macOS/Linux use `curl` instead of `curl.exe`.)

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /transactions | List all transactions |
| GET | /transactions/{id} | Get one transaction |
| POST | /transactions | Add a transaction |
| PUT | /transactions/{id} | Update a transaction |
| DELETE | /transactions/{id} | Delete a transaction |

Full request and response examples are in `docs/api_docs.md`.

## DSA comparison

    python dsa/compare_search.py

Compares linear search (O(n)) with dictionary lookup (O(1) average) on 20 records and on the full dataset.

## Team

Team name: Group 11