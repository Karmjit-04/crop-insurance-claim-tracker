-- SQLite schema for PMFBY Crop Insurance Claim Tracker

CREATE TABLE IF NOT EXISTS claims (
    application_number TEXT PRIMARY KEY,
    farmer_name        TEXT NOT NULL,
    phone_number       TEXT,
    state              TEXT,
    district           TEXT,
    crop               TEXT NOT NULL,
    season             TEXT NOT NULL,
    sowing_date        TEXT,
    land_survey_no     TEXT,
    claim_status       TEXT NOT NULL,
    missing_document   TEXT DEFAULT 'None',
    payment_status     TEXT NOT NULL,
    approved_amount    REAL DEFAULT 0.0,
    paid_amount        REAL DEFAULT 0.0,
    bank_reference_id  TEXT,
    last_updated       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    application_number TEXT NOT NULL,
    step_name          TEXT NOT NULL,
    severity           TEXT DEFAULT 'INFO',
    finding            TEXT,
    raw_evidence       TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approval_requests (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    application_number TEXT NOT NULL,
    action_type        TEXT NOT NULL,
    previous_value     TEXT,
    proposed_value     TEXT,
    reason             TEXT,
    status             TEXT DEFAULT 'PENDING',
    approved_by        TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_results (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id           TEXT NOT NULL,
    test_name              TEXT NOT NULL,
    status                 TEXT NOT NULL,
    execution_time_seconds REAL,
    details                TEXT,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
