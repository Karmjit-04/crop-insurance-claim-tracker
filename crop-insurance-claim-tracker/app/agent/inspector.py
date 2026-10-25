"""
Inspection and validation reasoning engine for crop insurance claims.
Identifies discrepancies, missing documents, season mismatches, and disbursal safety rules.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agent.i18n import get_claim_summary_localized, get_text
from database import db


# Agricultural rules dictionary for season validation (India PMFBY Standards)
CROP_SEASON_RULES = {
    "wheat": {"typical_season": "Rabi", "valid_sowing_months": [10, 11, 12, 1]},
    "mustard": {"typical_season": "Rabi", "valid_sowing_months": [10, 11, 12]},
    "gram": {"typical_season": "Rabi", "valid_sowing_months": [10, 11, 12]},
    "barley": {"typical_season": "Rabi", "valid_sowing_months": [10, 11, 12]},
    "paddy": {"typical_season": "Kharif", "valid_sowing_months": [5, 6, 7, 8]},
    "paddy (rice)": {"typical_season": "Kharif", "valid_sowing_months": [5, 6, 7, 8]},
    "cotton": {"typical_season": "Kharif", "valid_sowing_months": [4, 5, 6, 7]},
    "soybean": {"typical_season": "Kharif", "valid_sowing_months": [6, 7, 8]},
    "maize": {"typical_season": "Kharif", "valid_sowing_months": [6, 7, 8]},
}


def read_claim_status_in_language(claim_data: Dict[str, Any], lang: str = "hi") -> Dict[str, Any]:
    """
    Test Case 1 (TC1):
    Reads current claim status in the farmer's Hindi language with zero distortion.
    """
    summary = get_claim_summary_localized(claim_data, lang="hi")
    
    # Store evidence in SQLite
    finding = f"Language: HINDI | Claim Status: {summary['claim_status_text']} | Payment: {summary['payment_status_text']}"
    db.log_evidence(
        app_no=claim_data.get("application_number", "UNKNOWN"),
        step_name="TC1_READ_STATUS_LOCALIZED",
        finding=finding,
        severity="INFO",
        raw_evidence=str(summary),
    )
    return summary


def identify_missing_land_documents(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test Case 2 (TC2):
    Identifies the exact missing land document from claim state or DOM data.
    """
    app_no = claim_data.get("application_number", "")
    claim_status = claim_data.get("claim_status", "")
    missing_doc = claim_data.get("missing_document", "None")

    is_missing = False
    exact_doc = None
    severity = "INFO"
    recommendation = "All required land records are present and verified."

    if claim_status == "DOCUMENTS_REQUIRED" or (missing_doc and missing_doc.lower() != "none"):
        is_missing = True
        exact_doc = missing_doc if missing_doc.lower() != "none" else "Record of Rights (RoR / Khasra-Khatauni)"
        severity = "WARNING"
        recommendation = (
            f"Action Required: Upload official '{exact_doc}' for Survey No. {claim_data.get('land_survey_no', 'N/A')}. "
            f"Human approval required before portal document submission."
        )

    finding = f"Missing Document Check: is_missing={is_missing}, exact_document='{exact_doc}'"
    db.log_evidence(
        app_no=app_no,
        step_name="TC2_IDENTIFY_MISSING_LAND_DOC",
        finding=finding,
        severity=severity,
        raw_evidence=f"Status: {claim_status}, Land Record: {exact_doc}",
    )

    return {
        "application_number": app_no,
        "is_missing": is_missing,
        "exact_missing_document": exact_doc,
        "recommendation": recommendation,
        "survey_no": claim_data.get("land_survey_no", ""),
    }


def detect_season_discrepancy(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test Case 3 (TC3):
    Detects an incorrect season based on crop type and sowing date, and proposes a correction.
    Requires explicit human approval before any change is made.
    """
    app_no = claim_data.get("application_number", "")
    crop_name = claim_data.get("crop", "").strip().lower()
    current_season = claim_data.get("season", "").strip()
    sowing_date_str = claim_data.get("sowing_date", "")

    mismatch_detected = False
    proposed_season = None
    reason = "Season matches crop agronomic cycle."

    try:
        sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d")
        month = sowing_date.month
        year = sowing_date.year
    except Exception:
        month = None
        year = 2025

    # Check known crop agronomic rules
    matched_rule = None
    for key, rule in CROP_SEASON_RULES.items():
        if key in crop_name:
            matched_rule = rule
            break

    if matched_rule and month:
        expected_type = matched_rule["typical_season"]  # "Rabi" or "Kharif"
        
        # Determine actual crop season from sowing month
        if month in [10, 11, 12, 1, 2]:
            correct_season_type = "Rabi"
            correct_season_label = f"Rabi {year}-{str(year + 1)[-2:]}"
        else:
            correct_season_type = "Kharif"
            correct_season_label = f"Kharif {year}"

        # If portal season doesn't match the agronomic season
        if correct_season_type.lower() not in current_season.lower():
            mismatch_detected = True
            proposed_season = correct_season_label
            reason = (
                f"Agronomic Mismatch: {claim_data.get('crop')} sown on {sowing_date_str} (month {month}) "
                f"falls in the {correct_season_type} season, but portal records '{current_season}'."
            )

    severity = "WARNING" if mismatch_detected else "INFO"
    finding = (
        f"Season Check: mismatch={mismatch_detected}, current='{current_season}', proposed='{proposed_season}'"
    )
    db.log_evidence(
        app_no=app_no,
        step_name="TC3_DETECT_SEASON_MISMATCH",
        finding=finding,
        severity=severity,
        raw_evidence=reason,
    )

    approval_id = None
    if mismatch_detected and proposed_season:
        # Create Human-in-the-loop pending approval request
        approval_id = db.create_approval_request(
            app_no=app_no,
            action_type="SEASON_CORRECTION",
            prev_val=current_season,
            prop_val=proposed_season,
            reason=reason,
        )

    return {
        "application_number": app_no,
        "mismatch_detected": mismatch_detected,
        "current_season": current_season,
        "proposed_season": proposed_season,
        "reason": reason,
        "approval_request_id": approval_id,
        "requires_human_approval": mismatch_detected,
    }


def verify_payment_disbursal_safety(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test Case 4 (TC4):
    Never report an approved claim as paid until bank credit is confirmed.
    Distinguishes:
      - APPROVED but bank processing (Money NOT yet in farmer's bank)
      - BANK_CREDIT_CONFIRMED (Money successfully deposited with UTR / reference)
    """
    app_no = claim_data.get("application_number", "")
    claim_status = claim_data.get("claim_status", "")
    payment_status = claim_data.get("payment_status", "")
    approved_amount = float(claim_data.get("approved_amount", 0.0))
    paid_amount = float(claim_data.get("paid_amount", 0.0))
    bank_ref = claim_data.get("bank_reference_id")

    is_approved = (claim_status == "APPROVED")
    is_credit_confirmed = (payment_status == "BANK_CREDIT_CONFIRMED" and paid_amount > 0 and bool(bank_ref))

    # CRITICAL INVARIANT: Can we report the money as paid to the farmer?
    # MUST BE FALSE if bank credit is not confirmed, even if approved!
    reported_as_paid = False

    if is_approved and not is_credit_confirmed:
        reported_as_paid = False
        display_status = "Approved - Pending Bank Credit Confirmation"
        safety_audit = "PASS: Approved claim correctly kept in 'Pending Bank Confirmation' state; NOT reported as paid."
        severity = "INFO"
    elif is_approved and is_credit_confirmed:
        reported_as_paid = True
        display_status = "Payment Disbursed & Bank Credit Confirmed"
        safety_audit = f"PASS: Claim verified paid with bank credit UTR: {bank_ref}."
        severity = "SUCCESS"
    else:
        reported_as_paid = False
        display_status = "Claim Pending Approval"
        safety_audit = "INFO: Claim is still in review/documentation stage."
        severity = "INFO"

    db.log_evidence(
        app_no=app_no,
        step_name="TC4_VERIFY_PAYMENT_SAFETY",
        finding=f"Safety Rule: approved={is_approved}, credit_confirmed={is_credit_confirmed}, reported_as_paid={reported_as_paid}",
        severity=severity,
        raw_evidence=safety_audit,
    )

    return {
        "application_number": app_no,
        "claim_status": claim_status,
        "payment_status": payment_status,
        "is_approved": is_approved,
        "is_credit_confirmed": is_credit_confirmed,
        "reported_as_paid": reported_as_paid,
        "display_status": display_status,
        "safety_audit": safety_audit,
        "approved_amount": approved_amount,
        "paid_amount": paid_amount,
        "bank_reference_id": bank_ref,
    }
