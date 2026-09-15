-- =====================================================================
-- MoMo SMS Analytics — database_setup.sql
-- Creates the schema for storing parsed MTN Mobile Money SMS transactions.
-- Engine: MySQL / MariaDB
-- =====================================================================

DROP DATABASE IF EXISTS momo_sms_analytics;
CREATE DATABASE momo_sms_analytics;
USE momo_sms_analytics;

-- ---------------------------------------------------------------------
-- Table: Transaction_Categories
-- Lookup table of transaction types (Incoming Money, Payment, etc.)
-- ---------------------------------------------------------------------
CREATE TABLE Transaction_Categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a transaction category',
    category_name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Human-readable category name, e.g. Incoming Money',
    description   VARCHAR(255) COMMENT 'Short explanation of what falls under this category'
) COMMENT 'Fixed lookup list of MoMo transaction types used by the ETL categorizer';

-- ---------------------------------------------------------------------
-- Table: Users
-- Senders/receivers referenced across transactions
-- ---------------------------------------------------------------------
CREATE TABLE Users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a user/customer/merchant',
    full_name    VARCHAR(100) NOT NULL COMMENT 'Name as it appears in the SMS body',
    phone_number VARCHAR(20) COMMENT 'Phone number, often partially masked in the source SMS',
    momo_code    VARCHAR(20) COMMENT 'Merchant/till code, only present for merchant-type users',
    user_type    ENUM('customer', 'merchant', 'agent', 'system') NOT NULL DEFAULT 'customer'
        COMMENT 'Classification of the user based on how they appear in transactions'
) COMMENT 'People and entities that send or receive money in MoMo transactions';

-- ---------------------------------------------------------------------
-- Table: Transactions
-- Core fact table — one row per parsed MoMo transaction
-- ---------------------------------------------------------------------
CREATE TABLE Transactions (
    transaction_id            INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a transaction record',
    category_id               INT NOT NULL COMMENT 'FK to Transaction_Categories',
    financial_transaction_id  VARCHAR(30) UNIQUE COMMENT 'MTN-issued Financial Transaction Id, unique when present',
    external_transaction_id   VARCHAR(30) COMMENT 'External TxId reference, when the SMS provides one',
    amount                    DECIMAL(12,2) NOT NULL COMMENT 'Transaction amount in the given currency',
    fee                       DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Fee charged for the transaction, if any',
    balance_after              DECIMAL(12,2) COMMENT 'Account balance after the transaction, when disclosed in the SMS',
    currency                  CHAR(3) NOT NULL DEFAULT 'RWF' COMMENT 'ISO-like currency code, defaults to Rwandan Franc',
    transaction_datetime       DATETIME NOT NULL COMMENT 'Date/time the transaction occurred, parsed from the SMS body',
    sms_date_received         DATETIME COMMENT 'Date/time the SMS itself was received on-device',
    status                     ENUM('completed', 'failed', 'pending') NOT NULL DEFAULT 'completed'
        COMMENT 'Outcome of the transaction as reported by the SMS',
    raw_body                  TEXT COMMENT 'Original SMS text, retained for audit/debugging',
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id) REFERENCES Transaction_Categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_transactions_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_transactions_fee_nonnegative CHECK (fee >= 0)
) COMMENT 'One row per successfully parsed MoMo SMS transaction';

-- ---------------------------------------------------------------------
-- Table: Transaction_Participants  (junction table, resolves M:N)
-- Links Transactions <-> Users, tagging each link with a role
-- ---------------------------------------------------------------------
CREATE TABLE Transaction_Participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a participant link',
    transaction_id INT NOT NULL COMMENT 'FK to Transactions',
    user_id        INT NOT NULL COMMENT 'FK to Users',
    role           ENUM('sender', 'receiver') NOT NULL COMMENT 'Whether this user sent or received funds in the transaction',
    CONSTRAINT fk_participants_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_participants_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_participant_role UNIQUE (transaction_id, user_id, role)
) COMMENT 'Junction table resolving the many-to-many relationship between Transactions and Users';

-- ---------------------------------------------------------------------
-- Table: System_Logs
-- ETL processing/audit log, including entries for unparseable SMS
-- ---------------------------------------------------------------------
CREATE TABLE System_Logs (
    log_id         INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for a log entry',
    transaction_id INT COMMENT 'FK to Transactions, nullable when the SMS never became a transaction',
    raw_sms_id     VARCHAR(50) COMMENT 'Reference to the source SMS record, used when parsing fails',
    log_level      ENUM('info', 'warning', 'error') NOT NULL DEFAULT 'info' COMMENT 'Severity of the log entry',
    message        VARCHAR(255) NOT NULL COMMENT 'Human-readable log message',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When the log entry was written',
    CONSTRAINT fk_logs_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) COMMENT 'ETL pipeline audit trail, including parse failures routed to the dead-letter path';

-- ---------------------------------------------------------------------
-- Indexes for common query patterns
-- ---------------------------------------------------------------------
CREATE INDEX idx_transactions_datetime ON Transactions(transaction_datetime);
CREATE INDEX idx_transactions_category ON Transactions(category_id);
CREATE INDEX idx_participants_transaction ON Transaction_Participants(transaction_id);
CREATE INDEX idx_participants_user ON Transaction_Participants(user_id);
CREATE INDEX idx_logs_transaction ON System_Logs(transaction_id);
CREATE INDEX idx_users_phone ON Users(phone_number);

-- =====================================================================
-- Sample data
-- =====================================================================


-- ---------------------------------------------------------------------
-- Transaction_Categories
-- ---------------------------------------------------------------------
INSERT INTO Transaction_Categories (category_name, description) VALUES
('Incoming Money', 'Funds received from another person via MoMo'),
('Payment', 'Payment made to a person or merchant code'),
('Bank Deposit', 'Cash deposited into the MoMo account via a bank/agent'),
('Transfer to Mobile Number', 'Direct transfer sent to another mobile number'),
('Airtime Purchase', 'Airtime bought using MoMo balance'),
('Data Bundle Purchase', 'Mobile data bundle bought using MoMo balance');

-- ---------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------
INSERT INTO Users (full_name, phone_number, momo_code, user_type) VALUES
('Jane Smith', '+250788110001', NULL, 'customer'),
('Samuel Carter', '+250788110002', NULL, 'customer'),
('Alex Doe', '+250788110003', NULL, 'customer'),
('Robert Brown', '+250788110004', '12845', 'merchant'),
('MTN Rwanda', NULL, 'AIRTIME01', 'system'),
('Linda Green', '+250788110005', NULL, 'customer');

-- ---------------------------------------------------------------------
-- Transactions
-- ---------------------------------------------------------------------
INSERT INTO Transactions
    (category_id, financial_transaction_id, external_transaction_id, amount, fee, balance_after,
     currency, transaction_datetime, sms_date_received, status, raw_body)
VALUES
    (1, 'FTX10001', NULL, 20000.00, 0.00, 35000.00,
     'RWF', '2024-05-10 14:32:00', '2024-05-10 14:32:05', 'completed',
     'You have received 20000 RWF from Jane Smith. Financial Transaction Id: FTX10001'),
    (2, 'FTX10002', 'TXN2002', 5000.00, 100.00, 30000.00,
     'RWF', '2024-05-11 09:15:00', '2024-05-11 09:15:03', 'completed',
     'TxId: TXN2002. Your payment of 5000 RWF to Robert Brown 12845 has been completed'),
    (3, NULL, NULL, 50000.00, 0.00, 80000.00,
     'RWF', '2024-05-12 11:00:00', '2024-05-12 11:00:04', 'completed',
     '*113*R*A bank deposit of 50000 RWF has been added to your account via Cash Deposit'),
    (4, 'FTX10003', NULL, 8000.00, 50.00, 72000.00,
     'RWF', '2024-05-13 16:45:00', '2024-05-13 16:45:02', 'completed',
     '*165*S*8000 RWF transferred to Samuel Carter (+250788110002) from your account'),
    (5, 'FTX10004', NULL, 1000.00, 0.00, 71000.00,
     'RWF', '2024-05-14 08:20:00', '2024-05-14 08:20:01', 'completed',
     '*162*TxId:FTX10004*S*Your payment of 1000 RWF to Airtime with token has been completed'),
    (6, 'FTX10005', 'TXN2006', 2000.00, 0.00, 69000.00,
     'RWF', '2024-05-15 19:05:00', '2024-05-15 19:05:03', 'completed',
     '*164*S*Your transaction of 2000 RWF by Data Bundle MTN completed. Financial Transaction Id: FTX10005 External Transaction Id: TXN2006');

-- ---------------------------------------------------------------------
-- Transaction_Participants
-- ---------------------------------------------------------------------
INSERT INTO Transaction_Participants (transaction_id, user_id, role) VALUES
(1, 1, 'sender'),    -- Jane Smith sends incoming money to the account owner
(1, 3, 'receiver'),  -- Alex Doe = account owner receiving
(2, 3, 'sender'),    -- Alex Doe pays
(2, 4, 'receiver'),  -- Robert Brown (merchant) receives payment
(3, 3, 'receiver'),  -- Alex Doe receives the bank deposit
(4, 3, 'sender'),    -- Alex Doe transfers out
(4, 2, 'receiver'),  -- Samuel Carter receives transfer
(5, 3, 'sender'),    -- Alex Doe buys airtime
(5, 5, 'receiver'),  -- MTN Rwanda (system) receives airtime payment
(6, 3, 'sender'),    -- Alex Doe buys data bundle
(6, 5, 'receiver');  -- MTN Rwanda (system) receives bundle payment

-- ---------------------------------------------------------------------
-- System_Logs
-- ---------------------------------------------------------------------
INSERT INTO System_Logs (transaction_id, raw_sms_id, log_level, message) VALUES
(1, 'SMS-0001', 'info', 'Transaction parsed and inserted successfully'),
(2, 'SMS-0002', 'info', 'Transaction parsed and inserted successfully'),
(3, 'SMS-0003', 'info', 'Transaction parsed and inserted successfully'),
(NULL, 'SMS-0007', 'warning', 'SMS matched no known transaction pattern (promotional bundle offer)'),
(NULL, 'SMS-0008', 'error', 'Failed to extract amount field from SMS body'),
(6, 'SMS-0006', 'info', 'Transaction parsed and inserted successfully');