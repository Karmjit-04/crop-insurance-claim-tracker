"""
Official Test Suite for Agentic AI Hackathon 2026.
Contains all four required test cases:
  - TC1: Read current claim status in the farmer's chosen language.
  - TC2: Identify the exact missing land document.
  - TC3: Detect an incorrect season and propose a correction (with HITL gate).
  - TC4: Never report an approved claim as paid until credit is confirmed.
"""

import time
import pytest
from database import db
from agent.inspector import (
    read_claim_status_in_language,
    identify_missing_land_documents,
    detect_season_discrepancy,
    verify_payment_disbursal_safety,
)
from agent.runner import PortalAgentRunner


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database is seeded with synthetic test cases before running."""
    db.init_db(seed_synthetic=True)


def test_tc1_hindi_claim_status():
    """
    TC1: Read current claim status in the farmer's chosen language (Hindi).
    Asserts authentic localized Hindi terminology without translation distortion.
    """
    start_time = time.time()
    claim = db.get_claim("CROP-2026-TC1")
    assert claim is not None, "Test claim CROP-2026-TC1 not found in database"

    # Verify claim status in Hindi
    hi_summary = read_claim_status_in_language(claim, lang="hi")
    assert "स्वीकृत" in hi_summary["claim_status_text"], f"Hindi status missing expected text: {hi_summary['claim_status_text']}"
    assert "जमा" in hi_summary["payment_status_text"], f"Hindi payment missing expected text: {hi_summary['payment_status_text']}"
    assert hi_summary["language"] == "hi"
    assert "सत्यापित" in hi_summary["missing_document_text"]

    duration = round(time.time() - start_time, 3)
    db.log_test_result(
        test_case_id="TC1",
        test_name="Hindi Claim Status Reading",
        status="PASS",
        duration=duration,
        details=f"Verified Hindi status ('{hi_summary['claim_status_text']}') and payment ('{hi_summary['payment_status_text']}').",
    )


def test_tc2_identify_exact_missing_land_document():
    """
    TC2: Identify the exact missing land document.
    Pinpoints Record of Rights (RoR / Khasra-Khatauni) for Land Survey No. SURV-208/B.
    """
    start_time = time.time()
    claim = db.get_claim("CROP-2026-TC2")
    assert claim is not None, "Test claim CROP-2026-TC2 not found"

    result = identify_missing_land_documents(claim)
    assert result["is_missing"] is True, "Agent failed to identify missing document state"
    assert "Record of Rights" in result["exact_missing_document"], f"Unexpected missing document: {result['exact_missing_document']}"
    assert result["survey_no"] == "SURV-208/B"
    assert "Action Required" in result["recommendation"]

    # Verify evidence was recorded in SQLite
    logs = db.get_evidence_logs("CROP-2026-TC2")
    assert len(logs) > 0, "Evidence log not recorded in SQLite"
    assert any("TC2_IDENTIFY_MISSING_LAND_DOC" in l["step_name"] for l in logs)

    duration = round(time.time() - start_time, 3)
    db.log_test_result(
        test_case_id="TC2",
        test_name="Identify Exact Missing Land Document",
        status="PASS",
        duration=duration,
        details=f"Identified '{result['exact_missing_document']}' for Survey {result['survey_no']}.",
    )


def test_tc3_detect_season_mismatch_and_propose_correction():
    """
    TC3: Detect an incorrect season and propose a correction.
    Wheat sown in November 2025 cannot be Kharif. Proposes Rabi 2025-26.
    Ensures safety gate blocks execution until human approval is recorded in SQLite.
    """
    start_time = time.time()
    claim = db.get_claim("CROP-2026-TC3")
    assert claim is not None, "Test claim CROP-2026-TC3 not found"
    assert claim["crop"] == "Wheat"
    assert claim["season"] == "Kharif 2025"

    # Step 1: Detect discrepancy
    detection = detect_season_discrepancy(claim)
    assert detection["mismatch_detected"] is True, "Failed to detect season mismatch"
    assert "Rabi" in detection["proposed_season"], f"Proposed wrong season: {detection['proposed_season']}"
    assert detection["requires_human_approval"] is True

    # Step 2: Verify approval request created in SQLite with status 'PENDING'
    approval_id = detection["approval_request_id"]
    assert approval_id is not None
    pending_approvals = db.get_approval_requests(status="PENDING")
    req = next((r for r in pending_approvals if r["id"] == approval_id), None)
    assert req is not None, "Approval request not saved in SQLite"
    assert req["status"] == "PENDING"

    # Step 3: Verify safety gate blocks execution when approval is pending
    runner = PortalAgentRunner()
    blocked_exec = runner.execute_season_correction("CROP-2026-TC3", detection["proposed_season"])
    assert blocked_exec["status"] == "PENDING"
    assert "blocked" in blocked_exec["message"].lower()

    # Step 4: Human grants explicit approval
    db.resolve_approval_request(approval_id, decision="APPROVED", approved_by="Farmer Anil Sharma")

    # Step 5: Direct update & Re-read verification
    db.update_claim_season("CROP-2026-TC3", detection["proposed_season"])
    updated_claim = db.get_claim("CROP-2026-TC3")
    assert updated_claim["season"] == "Rabi 2025-26"

    # Re-inspect to confirm discrepancy is resolved
    post_check = detect_season_discrepancy(updated_claim)
    assert post_check["mismatch_detected"] is False, "Discrepancy should be cleared after update"

    duration = round(time.time() - start_time, 3)
    db.log_test_result(
        test_case_id="TC3",
        test_name="Detect Season Mismatch & HITL Safe Correction",
        status="PASS",
        duration=duration,
        details="Wheat season mismatch detected. Human approval safety gate verified. Correction re-read and validated.",
    )


def test_tc4_never_report_approved_as_paid_until_credit_confirmed():
    """
    TC4: Never report an approved claim as paid until credit is confirmed.
    Ensures that when claim_status == APPROVED but payment_status == UNDER_BANK_PROCESSING,
    the agent strictly reports 'Pending Bank Confirmation' and reported_as_paid == False.
    """
    start_time = time.time()
    claim = db.get_claim("CROP-2026-TC4")
    assert claim is not None, "Test claim CROP-2026-TC4 not found"
    assert claim["claim_status"] == "APPROVED"
    assert claim["payment_status"] == "UNDER_BANK_PROCESSING"

    verification = verify_payment_disbursal_safety(claim)
    assert verification["is_approved"] is True, "Claim must be in approved status"
    assert verification["is_credit_confirmed"] is False, "Credit must NOT be confirmed"
    assert verification["reported_as_paid"] is False, "CRITICAL SAFETY VIOLATION: Claim reported as paid before bank credit!"
    assert "Pending Bank Credit Confirmation" in verification["display_status"]

    # Verify contrast with confirmed claim (TC1)
    tc1_claim = db.get_claim("CROP-2026-TC1")
    tc1_verification = verify_payment_disbursal_safety(tc1_claim)
    assert tc1_verification["is_credit_confirmed"] is True
    assert tc1_verification["reported_as_paid"] is True

    duration = round(time.time() - start_time, 3)
    db.log_test_result(
        test_case_id="TC4",
        test_name="Payment Disbursal Safety Invariant (Approved != Paid)",
        status="PASS",
        duration=duration,
        details="Enforced zero false payment confirmations. Approved claims in bank queue remain pending.",
    )
