"""
Unified Flask Application for Crop Insurance Claim Tracker (Agentic AI Hackathon 2026).
Hosts:
  1. Farmer-friendly Dashboard (with multi-language support: hi, pa, mr, te, en)
  2. Local Mock Insurance Portal (Krishi Bima Seva with Playwright targets)
  3. Human-in-the-Loop (HITL) Approvals Center
  4. Real-time REST API for Playwright Agent interactions
"""

import os
from flask import Flask, jsonify, redirect, render_template, request, url_for

from agent.i18n import get_claim_summary_localized, get_text
from agent.inspector import (
    detect_season_discrepancy,
    identify_missing_land_documents,
    read_claim_status_in_language,
    verify_payment_disbursal_safety,
)
from agent.runner import PortalAgentRunner
from database import db
from run_tests import run_all_official_tests

app = Flask(__name__)
app.secret_key = "crop-insurance-tracker-hackathon-2026-secret-key"

# Ensure SQLite tables and baseline data exist
db.init_db(seed_synthetic=True)


@app.context_processor
def inject_i18n():
    pending = len(db.get_approval_requests(status="PENDING"))
    return {
        "lang": "hi",
        "pending_count": pending,
        "t": lambda key: get_text(key, lang="hi"),
    }


# ==============================================================================
# FARMER-FRIENDLY DASHBOARD ROUTES
# ==============================================================================

@app.route("/")
def dashboard():
    raw_claims = db.get_all_claims()
    localized_claims = [get_claim_summary_localized(c, lang="hi") for c in raw_claims]
    return render_template("dashboard.html", claims=localized_claims, lang="hi")


@app.route("/approvals")
def approvals():
    pending = db.get_approval_requests(status="PENDING")
    resolved = [r for r in db.get_approval_requests() if r["status"] != "PENDING"]
    return render_template(
        "approvals.html",
        pending_approvals=pending,
        resolved_history=resolved,
        lang="hi",
    )


@app.route("/tests")
def tests_view():
    history = db.get_latest_test_results()
    return render_template("tests_view.html", test_history=history, lang="hi")


# ==============================================================================
# LOCAL MOCK INSURANCE PORTAL ROUTES (Target for Playwright)
# ==============================================================================

@app.route("/portal/claim/<app_no>")
def portal_claim(app_no):
    claim = db.get_claim(app_no)
    if not claim:
        return f"<h3>Claim {app_no} not found on Mock Insurance Portal</h3>", 404

    msg = request.args.get("msg")
    msg_type = request.args.get("msg_type", "info")
    return render_template("portal_claim.html", claim=claim, msg=msg, msg_type=msg_type)


@app.route("/portal/claim/<app_no>/edit-season", methods=["POST"])
def portal_edit_season(app_no):
    new_season = request.form.get("new_season", "").strip()
    if new_season:
        db.update_claim_season(app_no, new_season)
        db.log_evidence(
            app_no=app_no,
            step_name="PORTAL_SEASON_MUTATION",
            finding=f"Mock portal season changed to '{new_season}'.",
            severity="INFO",
        )
        return redirect(url_for("portal_claim", app_no=app_no, msg=f"Season updated to {new_season}", msg_type="success"))
    return redirect(url_for("portal_claim", app_no=app_no, msg="Invalid season selection", msg_type="danger"))


@app.route("/portal/claim/<app_no>/upload-doc", methods=["POST"])
def portal_upload_doc(app_no):
    document_name = request.form.get("document_name", "").strip()
    if document_name:
        # Clear missing doc and set status to UNDER_REVIEW
        db.update_claim_missing_document(app_no, missing_doc="None", new_status="UNDER_REVIEW")
        db.log_evidence(
            app_no=app_no,
            step_name="PORTAL_DOCUMENT_UPLOAD",
            finding=f"Uploaded '{document_name}'. Missing deficiency cleared.",
            severity="SUCCESS",
        )
        return redirect(url_for("portal_claim", app_no=app_no, msg=f"Document '{document_name}' uploaded successfully!", msg_type="success"))
    return redirect(url_for("portal_claim", app_no=app_no, msg="Document name required", msg_type="danger"))


# ==============================================================================
# REST API FOR AGENT & AUTOMATION
# ==============================================================================

@app.route("/api/claims", methods=["GET"])
def api_get_claims():
    raw = db.get_all_claims()
    return jsonify([get_claim_summary_localized(c, lang="hi") for c in raw])


@app.route("/api/claims/<app_no>", methods=["GET"])
def api_get_claim(app_no):
    claim = db.get_claim(app_no)
    if not claim:
        return jsonify({"error": "Claim not found"}), 404
    return jsonify(get_claim_summary_localized(claim, lang="hi"))


@app.route("/api/agent/scan/<app_no>", methods=["POST"])
def api_agent_scan(app_no):
    claim = db.get_claim(app_no)
    if not claim:
        return jsonify({"success": False, "error": f"Claim {app_no} not found"}), 404

    # Run inspector rules in Hindi
    tc1 = read_claim_status_in_language(claim, lang="hi")
    tc2 = identify_missing_land_documents(claim)
    tc3 = detect_season_discrepancy(claim)
    tc4 = verify_payment_disbursal_safety(claim)

    return jsonify({
        "success": True,
        "application_number": app_no,
        "result": {
            "tc1_language_status": tc1,
            "tc2_missing_docs": tc2,
            "tc3_season_check": tc3,
            "tc4_payment_safety": tc4,
        }
    })


@app.route("/api/agent/apply-season/<app_no>", methods=["POST"])
def api_agent_apply_season(app_no):
    data = request.get_json(silent=True) or {}
    new_season = data.get("new_season")
    if not new_season:
        return jsonify({"success": False, "error": "new_season is required"}), 400

    runner = PortalAgentRunner()
    result = runner.execute_season_correction(app_no, new_season)
    return jsonify({"success": True, "result": result})


@app.route("/api/agent/apply-doc/<app_no>", methods=["POST"])
def api_agent_apply_doc(app_no):
    data = request.get_json(silent=True) or {}
    doc_name = data.get("document_name", "Record of Rights (RoR / 7/12 Extract)")

    runner = PortalAgentRunner()
    result = runner.execute_document_upload(app_no, doc_name)
    return jsonify({"success": True, "result": result})


@app.route("/api/approvals/propose-doc", methods=["POST"])
def api_propose_doc():
    data = request.get_json(silent=True) or {}
    app_no = data.get("application_number")
    doc_name = data.get("document_name", "Record of Rights (RoR / 7/12 Extract)")
    if not app_no:
        return jsonify({"success": False, "error": "application_number required"}), 400

    claim = db.get_claim(app_no)
    prev = claim.get("missing_document", "None") if claim else "None"
    req_id = db.create_approval_request(
        app_no=app_no,
        action_type="DOCUMENT_UPLOAD",
        prev_val=prev,
        prop_val=doc_name,
        reason=f"Resolve deficient land documentation for Survey {claim.get('land_survey_no', 'N/A')}.",
    )
    return jsonify({"success": True, "request_id": req_id})


@app.route("/api/approvals/<int:req_id>/resolve", methods=["POST"])
def api_resolve_approval(req_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision", "APPROVED")
    approved_by = data.get("approved_by", "Farmer / Official")

    success = db.resolve_approval_request(req_id, decision=decision, approved_by=approved_by)
    return jsonify({"success": success})


@app.route("/api/run-tests", methods=["POST"])
def api_run_tests():
    success = run_all_official_tests()
    latest_results = db.get_latest_test_results()
    return jsonify({
        "success": True,
        "all_passed": success,
        "results": [
            {
                "test_case_id": r["test_case_id"],
                "test_name": r["test_name"],
                "status": r["status"],
                "duration": r["execution_time_seconds"],
                "details": r["details"],
            }
            for r in latest_results
        ]
    })


@app.route("/api/evidence", methods=["GET"])
def api_get_evidence():
    app_no = request.args.get("application_number")
    logs = db.get_evidence_logs(app_no=app_no)
    return jsonify(logs)


@app.route("/api/test-results", methods=["GET"])
def api_get_test_results():
    results = db.get_latest_test_results()
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🌾 Starting PMFBY Crop Tracker on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
