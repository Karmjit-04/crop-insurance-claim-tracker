"""
Hindi-Only Language Engine for PMFBY Crop Insurance Claim Tracker.
Provides authentic Hindi terminology for Indian farmers (खसरा-खतौनी, दावा स्वीकृत, आदि).
"""

from typing import Any, Dict

HINDI_TRANSLATIONS: Dict[str, str] = {
    "app_title": "पीएमएफबीवाई किसान दावा पोर्टल एवं ट्रैकर",
    "farmer_portal": "किसान दावा पोर्टल",
    "mock_portal": "सरकारी बीमा पोर्टल",
    "application_no": "आवेदन संख्या",
    "farmer_name": "किसान का नाम",
    "crop": "फसल",
    "season": "मौसम / सीजन",
    "sowing_date": "बुवाई की तारीख",
    "survey_no": "भूमि खसरा / सर्वे संख्या",
    "claim_status": "दावे की स्थिति",
    "missing_document": "अनुपलब्ध भूमि दस्तावेज",
    "payment_status": "भुगतान की स्थिति",
    "approved_amount": "स्वीकृत राशि",
    "paid_amount": "बैंक खाते में जमा राशि",
    "bank_ref": "बैंक संदर्भ संख्या / यूटीआर",
    "actions": "कार्रवाई",
    "status_SUBMITTED": "आवेदन जमा किया गया",
    "status_UNDER_REVIEW": "सत्यापन प्रक्रियाधीन है",
    "status_DOCUMENTS_REQUIRED": "कार्रवाई आवश्यक: दस्तावेज जमा करें",
    "status_APPROVED": "दावा समिति द्वारा स्वीकृत",
    "status_REJECTED": "दावा अस्वीकृत",
    "pay_PENDING_APPROVAL": "दावा अनुमोदन तक भुगतान लंबित",
    "pay_UNDER_BANK_PROCESSING": "दावा स्वीकृत - बैंक प्रक्रियाधीन (खाते में जमा होना बाकी)",
    "pay_BANK_CREDIT_CONFIRMED": "भुगतान पूर्ण - किसान के बैंक खाते में जमा",
    "no_missing_doc": "सभी दस्तावेज सत्यापित हैं",
    "doc_ror": "अधिकार अभिलेख (खसरा-खतौनी / जमाबंदी)",
    "human_approval_required": "मानव अनुमोदन आवश्यक है",
    "alert_missing_doc": "ध्यान दें: भूमि दस्तावेज गायब है! आगे बढ़ने के लिए अपलोड आवश्यक है।",
    "alert_season_mismatch": "चेतावनी: फसल और बुवाई का महीना चयनित मौसम से मेल नहीं खाते हैं।",
    "alert_approved_not_paid": "सूचना: दावा स्वीकृत हो गया है, लेकिन बैंक खाते में पैसा अभी तक नहीं पहुंचा है।",
    "test_cases": "स्वचालित परीक्षण",
    "run_all_tests": "एजेंटिक सत्यापन परीक्षण चलाएं",
    "pending_approvals": "लंबित मानवीय अनुमोदन",
    "approve_btn": "स्वीकृत करें",
    "reject_btn": "अस्वीकार करें",
    "portal_updated": "पोर्टल सफलतापूर्वक अद्यतन और पुनः सत्यापित किया गया।",
}


def get_text(key: str, lang: str = "hi") -> str:
    """Retrieves Hindi translated string."""
    return HINDI_TRANSLATIONS.get(key, key)


def get_claim_summary_localized(claim: Dict[str, Any], lang: str = "hi") -> Dict[str, str]:
    """
    Translates all dynamic claim attributes for display in Hindi.
    Specifically satisfies TC1: reading claim status in farmer's Hindi language.
    """
    status_key = f"status_{claim.get('claim_status', 'SUBMITTED')}"
    pay_key = f"pay_{claim.get('payment_status', 'PENDING_APPROVAL')}"

    missing_doc = claim.get("missing_document", "None")
    missing_doc_display = get_text("no_missing_doc", "hi")
    if missing_doc and missing_doc.lower() != "none":
        missing_doc_display = f"{get_text('doc_ror', 'hi')} ({missing_doc})"

    return {
        "application_number": claim.get("application_number", ""),
        "farmer_name": claim.get("farmer_name", ""),
        "crop": claim.get("crop", ""),
        "season": claim.get("season", ""),
        "sowing_date": claim.get("sowing_date", ""),
        "claim_status_code": claim.get("claim_status", ""),
        "claim_status_text": get_text(status_key, "hi"),
        "missing_document_text": missing_doc_display,
        "payment_status_code": claim.get("payment_status", ""),
        "payment_status_text": get_text(pay_key, "hi"),
        "approved_amount": f"₹{claim.get('approved_amount', 0.0):,.2f}",
        "paid_amount": f"₹{claim.get('paid_amount', 0.0):,.2f}",
        "bank_reference_id": claim.get("bank_reference_id") or "उपलब्ध नहीं (N/A)",
        "language": "hi",
    }
