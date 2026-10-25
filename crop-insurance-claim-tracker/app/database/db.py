"""
Database initialization, connections, and helper methods for Crop Insurance Claim Tracker.
Uses standard library sqlite3 (zero external dependencies).
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crop_tracker.db")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_synthetic: bool = True) -> None:
    """Initialize database tables and seed baseline synthetic data for hackathon test cases."""
    with get_connection() as conn:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        if seed_synthetic:
            seed_synthetic_data(conn)


def seed_synthetic_data(conn: sqlite3.Connection) -> None:
    """Seeds claims tailored specifically to the 4 hackathon test cases."""
    conn.execute("DELETE FROM approval_requests")
    conn.execute("DELETE FROM evidence_logs")
    synthetic_claims = [
        (
            "CROP-2026-TC1",
            "Ramesh Kumar",
            "9876543210",
            "Punjab",
            "Bathinda",
            "Paddy (Rice)",
            "Kharif 2025",
            "2025-06-20",
            "SURV-104/A",
            "APPROVED",
            "None",
            "BANK_CREDIT_CONFIRMED",
            42000.0,
            42000.0,
            "SBI-PMFBY-8921829",
        ),
        (
            "CROP-2026-TC2",
            "Sukhwinder Singh",
            "9812345678",
            "Punjab",
            "Mansa",
            "Cotton",
            "Kharif 2025",
            "2025-05-15",
            "SURV-208/B",
            "DOCUMENTS_REQUIRED",
            "Record of Rights (RoR / Khasra-Khatauni)",
            "PENDING_APPROVAL",
            0.0,
            0.0,
            None,
        ),
        (
            "CROP-2026-TC3",
            "Anil Sharma",
            "9765432109",
            "Haryana",
            "Sirsa",
            "Wheat",
            "Kharif 2025",  # Mismatch: Wheat sown in Nov is Rabi!
            "2025-11-15",
            "SURV-312/C",
            "UNDER_REVIEW",
            "None",
            "PENDING_APPROVAL",
            0.0,
            0.0,
            None,
        ),
        (
            "CROP-2026-TC4",
            "Balram Patel",
            "9654321098",
            "Madhya Pradesh",
            "Ujjain",
            "Soybean",
            "Kharif 2025",
            "2025-06-18",
            "SURV-419/D",
            "APPROVED",
            "None",
            "UNDER_BANK_PROCESSING",  # Approved, but bank credit not confirmed!
            55000.0,
            0.0,
            "NEFT-PENDING-ACK-902",
        ),
    ]

    cursor = conn.cursor()
    for claim in synthetic_claims:
        cursor.execute(
            """
            INSERT INTO claims (
                application_number, farmer_name, phone_number, state, district,
                crop, season, sowing_date, land_survey_no, claim_status,
                missing_document, payment_status, approved_amount, paid_amount,
                bank_reference_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(application_number) DO UPDATE SET
                farmer_name=excluded.farmer_name,
                phone_number=excluded.phone_number,
                state=excluded.state,
                district=excluded.district,
                crop=excluded.crop,
                season=excluded.season,
                sowing_date=excluded.sowing_date,
                land_survey_no=excluded.land_survey_no,
                claim_status=excluded.claim_status,
                missing_document=excluded.missing_document,
                payment_status=excluded.payment_status,
                approved_amount=excluded.approved_amount,
                paid_amount=excluded.paid_amount,
                bank_reference_id=excluded.bank_reference_id;
            """,
            claim,
        )
    conn.commit()


def get_all_claims() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM claims ORDER BY application_number").fetchall()
        return [dict(row) for row in rows]


def get_claim(application_number: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM claims WHERE application_number = ?",
            (application_number,),
        ).fetchone()
        return dict(row) if row else None


def update_claim_season(application_number: str, new_season: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE claims SET season = ?, last_updated = CURRENT_TIMESTAMP WHERE application_number = ?",
            (new_season, application_number),
        )
        conn.commit()
        return cur.rowcount > 0


def update_claim_missing_document(application_number: str, missing_doc: str, new_status: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE claims 
            SET missing_document = ?, claim_status = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE application_number = ?
            """,
            (missing_doc, new_status, application_number),
        )
        conn.commit()
        return cur.rowcount > 0


def log_evidence(app_no: str, step_name: str, finding: str, severity: str = "INFO", raw_evidence: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO evidence_logs (application_number, step_name, severity, finding, raw_evidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (app_no, step_name, severity, finding, raw_evidence),
        )
        conn.commit()
        return cur.lastrowid


def get_evidence_logs(app_no: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if app_no:
            rows = conn.execute(
                "SELECT * FROM evidence_logs WHERE application_number = ? ORDER BY id DESC",
                (app_no,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM evidence_logs ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def create_approval_request(app_no: str, action_type: str, prev_val: str, prop_val: str, reason: str) -> int:
    with get_connection() as conn:
        # Check if already pending
        existing = conn.execute(
            """
            SELECT id FROM approval_requests 
            WHERE application_number = ? AND action_type = ? AND status = 'PENDING'
            """,
            (app_no, action_type),
        ).fetchone()
        if existing:
            return existing["id"]

        cur = conn.execute(
            """
            INSERT INTO approval_requests (application_number, action_type, previous_value, proposed_value, reason, status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')
            """,
            (app_no, action_type, prev_val, prop_val, reason),
        )
        conn.commit()
        return cur.lastrowid


def resolve_approval_request(request_id: int, decision: str, approved_by: str = "Admin/Farmer") -> bool:
    """decision: 'APPROVED' or 'REJECTED'"""
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE approval_requests 
            SET status = ?, approved_by = ?, resolved_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (decision, approved_by, request_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_approval_requests(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM approval_requests WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM approval_requests ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def log_test_result(test_case_id: str, test_name: str, status: str, duration: float, details: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO test_results (test_case_id, test_name, status, execution_time_seconds, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (test_case_id, test_name, status, duration, details),
        )
        conn.commit()
        return cur.lastrowid


def get_latest_test_results() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t1.* FROM test_results t1
            INNER JOIN (
                SELECT test_case_id, MAX(id) as max_id FROM test_results GROUP BY test_case_id
            ) t2 ON t1.id = t2.max_id
            ORDER BY t1.test_case_id
            """
        ).fetchall()
        return [dict(row) for row in rows]
