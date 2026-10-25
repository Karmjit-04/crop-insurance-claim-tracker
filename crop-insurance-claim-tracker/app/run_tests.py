"""
Command-line test runner for Crop Insurance Claim Tracker (Hackathon 2026).
Executes all 4 official test cases, persists results in SQLite, and prints a formatted summary.
"""

import sys
import time
import io

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from database import db
from agent.inspector import (
    read_claim_status_in_language,
    identify_missing_land_documents,
    detect_season_discrepancy,
    verify_payment_disbursal_safety,
)
from agent.runner import PortalAgentRunner


def run_all_official_tests() -> bool:
    print("=" * 70)
    print("[TEST SUITE] PMFBY CROP INSURANCE CLAIM TRACKER")
    print("=" * 70)

    db.init_db(seed_synthetic=True)
    all_passed = True
    results = []

    # -------------------------------------------------------------
    # TC1: Read current claim status in farmer's Hindi language
    # -------------------------------------------------------------
    print("\n[RUNNING] TC1: Read claim status in Hindi...")
    t0 = time.time()
    try:
        claim = db.get_claim("CROP-2026-TC1")
        assert claim is not None, "CROP-2026-TC1 not found"

        hi = read_claim_status_in_language(claim, lang="hi")
        assert "स्वीकृत" in hi["claim_status_text"]
        assert "जमा" in hi["payment_status_text"]
        assert "सत्यापित" in hi["missing_document_text"]

        dur = round(time.time() - t0, 3)
        msg = f"Verified Hindi status ('{hi['claim_status_text']}') and payment ('{hi['payment_status_text']}') without translation distortion."
        db.log_test_result("TC1", "Hindi Claim Status Reading", "PASS", dur, msg)
        results.append(("TC1", "Hindi Claim Status", "PASS", dur, msg))
        print(f"  --> TC1 PASSED ({dur}s)")
    except Exception as e:
        dur = round(time.time() - t0, 3)
        all_passed = False
        db.log_test_result("TC1", "Multilingual Claim Status Reading", "FAIL", dur, str(e))
        results.append(("TC1", "Multilingual Status", "FAIL", dur, str(e)))
        print(f"  --> TC1 FAILED ({dur}s): {e}")

    # -------------------------------------------------------------
    # TC2: Identify exact missing land document
    # -------------------------------------------------------------
    print("\n[RUNNING] TC2: Identify exact missing land document...")
    t0 = time.time()
    try:
        claim = db.get_claim("CROP-2026-TC2")
        assert claim is not None, "CROP-2026-TC2 not found"

        inspection = identify_missing_land_documents(claim)
        assert inspection["is_missing"] is True, "Failed to identify missing document"
        assert "Record of Rights" in inspection["exact_missing_document"], f"Doc mismatch: {inspection['exact_missing_document']}"
        assert inspection["survey_no"] == "SURV-208/B"

        dur = round(time.time() - t0, 3)
        msg = f"Accurately identified '{inspection['exact_missing_document']}' for Survey {inspection['survey_no']}"
        db.log_test_result("TC2", "Identify Missing Land Document", "PASS", dur, msg)
        results.append(("TC2", "Missing Document Check", "PASS", dur, msg))
        print(f"  --> TC2 PASSED ({dur}s)")
    except Exception as e:
        dur = round(time.time() - t0, 3)
        all_passed = False
        db.log_test_result("TC2", "Identify Missing Land Document", "FAIL", dur, str(e))
        results.append(("TC2", "Missing Document Check", "FAIL", dur, str(e)))
        print(f"  --> TC2 FAILED ({dur}s): {e}")

    # -------------------------------------------------------------
    # TC3: Detect incorrect season and propose correction (HITL)
    # -------------------------------------------------------------
    print("\n[RUNNING] TC3: Detect season mismatch & enforce Human Approval gate...")
    t0 = time.time()
    try:
        claim = db.get_claim("CROP-2026-TC3")
        assert claim is not None, "CROP-2026-TC3 not found"
        assert claim["crop"] == "Wheat"
        assert claim["season"] == "Kharif 2025"

        detection = detect_season_discrepancy(claim)
        assert detection["mismatch_detected"] is True, "Failed to flag mismatch"
        assert "Rabi" in detection["proposed_season"]

        # Safety gate verification: block without approval
        runner = PortalAgentRunner()
        blocked_run = runner.execute_season_correction("CROP-2026-TC3", detection["proposed_season"])
        assert blocked_run["status"] == "PENDING", "Safety gate failed to block unauthorized update"

        # Explicit Human Approval
        approval_id = detection["approval_request_id"]
        db.resolve_approval_request(approval_id, decision="APPROVED", approved_by="Farmer Anil Sharma")

        # Update and re-read verification
        db.update_claim_season("CROP-2026-TC3", detection["proposed_season"])
        re_read_claim = db.get_claim("CROP-2026-TC3")
        assert re_read_claim["season"] == "Rabi 2025-26"
        assert detect_season_discrepancy(re_read_claim)["mismatch_detected"] is False

        dur = round(time.time() - t0, 3)
        msg = "Detected Wheat/Kharif mismatch -> Propose Rabi 2025-26 -> Enforced HITL gate -> Post-approval verified."
        db.log_test_result("TC3", "Detect Season Mismatch & HITL Gate", "PASS", dur, msg)
        results.append(("TC3", "Season Mismatch & HITL", "PASS", dur, msg))
        print(f"  --> TC3 PASSED ({dur}s)")
    except Exception as e:
        dur = round(time.time() - t0, 3)
        all_passed = False
        db.log_test_result("TC3", "Detect Season Mismatch & HITL Gate", "FAIL", dur, str(e))
        results.append(("TC3", "Season Mismatch & HITL", "FAIL", dur, str(e)))
        print(f"  --> TC3 FAILED ({dur}s): {e}")

    # -------------------------------------------------------------
    # TC4: Never report approved claim as paid until credit confirmed
    # -------------------------------------------------------------
    print("\n[RUNNING] TC4: Verify disbursal safety invariant (Approved != Paid)...")
    t0 = time.time()
    try:
        claim = db.get_claim("CROP-2026-TC4")
        assert claim is not None, "CROP-2026-TC4 not found"
        assert claim["claim_status"] == "APPROVED"
        assert claim["payment_status"] == "UNDER_BANK_PROCESSING"

        safety = verify_payment_disbursal_safety(claim)
        assert safety["is_approved"] is True
        assert safety["is_credit_confirmed"] is False
        assert safety["reported_as_paid"] is False, "INVARIANT VIOLATION: Claim reported as paid before bank credit!"
        assert "Pending Bank Credit Confirmation" in safety["display_status"]

        dur = round(time.time() - t0, 3)
        msg = "Invariant strictly upheld: Claim Approved + Bank Processing => Never reported as paid."
        db.log_test_result("TC4", "Disbursal Invariant Verification", "PASS", dur, msg)
        results.append(("TC4", "Disbursal Invariant", "PASS", dur, msg))
        print(f"  --> TC4 PASSED ({dur}s)")
    except Exception as e:
        dur = round(time.time() - t0, 3)
        all_passed = False
        db.log_test_result("TC4", "Disbursal Invariant Verification", "FAIL", dur, str(e))
        results.append(("TC4", "Disbursal Invariant", "FAIL", dur, str(e)))
        print(f"  --> TC4 FAILED ({dur}s): {e}")

    print("\n" + "=" * 70)
    print("FINAL TEST EXECUTION SUMMARY:")
    print("=" * 70)
    for tid, name, status, dur, detail in results:
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} [{tid}] {name:<26} : {status:<5} ({dur}s)")
        print(f"     Details: {detail}")

    print("=" * 70)
    if all_passed:
        print("🎉 ALL 4 OFFICIAL HACKATHON TEST CASES PASSED WITH 100% ACCURACY!")
    else:
        print("⚠️ SOME TEST CASES FAILED. Check details above.")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_all_official_tests()
    sys.exit(0 if success else 1)
