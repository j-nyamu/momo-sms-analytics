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

Team name: <your group 11>