# MoMo SMS Transactions API

Base URL: `http://localhost:8000`

## Authentication

Every endpoint uses HTTP Basic Authentication.

    Authorization: Basic base64(username:password)

Test credentials: `admin` / `password123`

A missing or wrong login returns `401 Unauthorized`.

## Transaction object

| Field | Type | Example |
|---|---|---|
| id | integer | 1 |
| transaction_type | string | "incoming_money" |
| amount | number | 2000 |
| currency | string | "RWF" |
| fee | number | 0 |
| balance_after | number | 2000 |
| sender | string | "Jane Smith" |
| receiver | string | "account owner" |
| timestamp | string | "2024-05-10T16:30:51" |
| financial_transaction_id | string | "76662021700" |
| status | string | "completed" |
| raw_body | string | Original SMS text |

---

## GET /transactions

Returns all transactions.

Request:

    curl.exe -u admin:password123 http://localhost:8000/transactions

Response `200 OK`:

    [
      { "id": 1, "transaction_type": "incoming_money", "amount": 2000, "...": "..." }
    ]

Errors: `401`

---

## GET /transactions/{id}

Returns one transaction.

Request:

    curl.exe -u admin:password123 http://localhost:8000/transactions/1

Response `200 OK`:

    {
      "id": 1,
      "transaction_type": "incoming_money",
      "amount": 2000,
      "currency": "RWF",
      "fee": 0,
      "balance_after": 2000,
      "sender": "Jane Smith",
      "receiver": "account owner",
      "timestamp": "2024-05-10T16:30:51",
      "financial_transaction_id": "76662021700",
      "status": "completed",
      "raw_body": "You have received 2000 RWF from Jane Smith ..."
    }

Errors: `401`, `404` (transaction not found)

---

## POST /transactions

Creates a transaction. `transaction_type` is required. The server assigns `id`.

Request body:

    {
      "transaction_type": "incoming_money",
      "amount": 5000,
      "currency": "RWF",
      "sender": "John Doe",
      "receiver": "account owner",
      "timestamp": "2024-06-01T10:00:00",
      "status": "completed"
    }

Response `201 Created`: the new transaction, including its `id`.

Errors: `400` (invalid JSON or missing `transaction_type`), `401`, `404`

---

## PUT /transactions/{id}

Updates the fields you send. Other fields stay unchanged. `id` cannot be changed.

Request body:

    { "amount": 7500, "status": "reviewed" }

Response `200 OK`: the updated transaction.

Errors: `400` (invalid JSON), `401`, `404` (transaction not found)

---

## DELETE /transactions/{id}

Deletes a transaction.

Request:

    curl.exe -u admin:password123 -X DELETE http://localhost:8000/transactions/2

Response `200 OK`:

    { "message": "Deleted", "id": 2 }

Errors: `401`, `404` (transaction not found)

---

## Error codes

| Code | Meaning |
|---|---|
| 200 | Request succeeded |
| 201 | Transaction created |
| 400 | Invalid JSON or missing required field |
| 401 | Missing or invalid credentials |
| 404 | Transaction or route not found |