# MoMo SMS Analytics

## Team 
- Members: Mungiiria Junior Nyamu, Ahmed Osman

## Team sheet
 link :https://docs.google.com/spreadsheets/d/1bHSBrGrJre_c2vXipDsf3vU5pD6qg8tCzz3ROFnCuW4/edit?usp=sharing

## Project Description
Processes MoMo (Mobile Money) SMS data from XML, cleans and categorizes
transactions, stores them in a relational database (MySQL/MariaDB), and
exposes a frontend dashboard for analysis and visualization.

## Architecture
High-level system architecture diagram: `docs/architecture_diagram.png`

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
Link: https://github.com/users/j-nyamu/projects/4/views/1

## Setup & Run
1. Run `database/database_setup.sql` against a local MySQL/MariaDB instance (see SQL Setup above)
2. Frontend and ETL setup instructions: TBD (added as those pieces are built)
