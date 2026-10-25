// Crop Insurance Claim Tracker Frontend Controller

async function runSingleAgentScan(appNo) {
    const card = document.getElementById(`claim-card-${appNo}`);
    if (card) {
        card.style.opacity = '0.6';
    }
    try {
        const res = await fetch(`/api/agent/scan/${appNo}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert(`✅ Agent Scan Complete for ${appNo}:\n\n` +
                  `Claim Status: ${data.result.tc1_language_status.claim_status_text}\n` +
                  `Missing Docs: ${data.result.tc2_missing_docs.exact_missing_document || 'None'}\n` +
                  `Season Valid: ${!data.result.tc3_season_check.mismatch_detected}\n` +
                  `Payment Safety: ${data.result.tc4_payment_safety.display_status}`);
            window.location.reload();
        } else {
            alert(`⚠️ Error during scan: ${data.error}`);
        }
    } catch (err) {
        alert(`Network Error: ${err.message}`);
    } finally {
        if (card) card.style.opacity = '1.0';
    }
}

async function runAllAgentScans() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerText = "⏳ Running Playwright scans...";

    try {
        const res = await fetch('/api/claims');
        const claims = await res.json();
        for (const claim of claims) {
            await fetch(`/api/agent/scan/${claim.application_number}`, { method: 'POST' });
        }
        alert("✅ All synthetic claims scanned by Playwright agent. Evidence recorded in SQLite.");
        window.location.reload();
    } catch (err) {
        alert(`Error running agent scans: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerText = "⚡ Scan All with Playwright Agent";
    }
}

async function requestDocumentUpload(appNo, docName) {
    if (!confirm(`Propose uploading '${docName}' for claim ${appNo} via Agent? This will create a pending Human Approval request.`)) {
        return;
    }
    try {
        const res = await fetch('/api/approvals/propose-doc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ application_number: appNo, document_name: docName })
        });
        const data = await res.json();
        if (data.success) {
            alert("🛡️ Proposal created! Navigating to Human Approval screen.");
            window.location.href = "/approvals";
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (err) {
        alert(`Network error: ${err.message}`);
    }
}

async function resolveApproval(id, decision, appNo, actionType, proposedVal) {
    const feedbackBox = document.getElementById(`feedback-${id}`);
    if (feedbackBox) {
        feedbackBox.style.display = 'block';
        feedbackBox.innerText = `⏳ Executing ${decision} decision and initiating Playwright browser action...`;
    }

    try {
        const res = await fetch(`/api/approvals/${id}/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision: decision, approved_by: 'Farmer / Admin' })
        });
        const data = await res.json();

        if (data.success) {
            if (decision === 'APPROVED') {
                // Now execute the verified agent action
                let execRes;
                if (actionType === 'SEASON_CORRECTION') {
                    execRes = await fetch(`/api/agent/apply-season/${appNo}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ new_season: proposedVal })
                    });
                } else if (actionType === 'DOCUMENT_UPLOAD') {
                    execRes = await fetch(`/api/agent/apply-doc/${appNo}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ document_name: proposedVal })
                    });
                }

                const execData = await execRes.json();
                alert(`Action Result: ${execData.result.status}\n\n${execData.result.message}`);
            } else {
                alert(`Action ${decision}. No portal changes were made.`);
            }
            window.location.reload();
        } else {
            alert(`Failed: ${data.error}`);
        }
    } catch (err) {
        alert(`Execution error: ${err.message}`);
    }
}

async function runAutomatedTestSuite() {
    const btn = document.getElementById('btn-run-tests');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "⏳ Executing 4 Official Test Cases via Playwright...";
    }

    // Set cards to testing
    ['tc1', 'tc2', 'tc3', 'tc4'].forEach(tc => {
        const el = document.getElementById(`${tc}-status`);
        if (el) {
            el.className = "test-status-indicator";
            el.innerText = "⏳ Testing...";
        }
    });

    try {
        const res = await fetch('/api/run-tests', { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            const results = data.results;
            results.forEach(r => {
                const tcKey = r.test_case_id.toLowerCase();
                const statusEl = document.getElementById(`${tcKey}-status`);
                const detailsEl = document.getElementById(`${tcKey}-details`);

                if (statusEl) {
                    if (r.status === 'PASS') {
                        statusEl.className = "test-status-indicator text-success font-bold";
                        statusEl.innerText = `✅ PASS (${r.duration}s)`;
                    } else {
                        statusEl.className = "test-status-indicator text-danger font-bold";
                        statusEl.innerText = `❌ FAIL (${r.duration}s)`;
                    }
                }
                if (detailsEl) {
                    detailsEl.innerText = r.details;
                }
            });
            alert("🎉 All 4 official test cases executed and recorded in SQLite!");
            setTimeout(() => window.location.reload(), 2000);
        } else {
            alert(`Test suite error: ${data.error}`);
        }
    } catch (err) {
        alert(`Network error running tests: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "▶️ Run All 4 Official Test Cases Now";
        }
    }
}

async function openEvidenceModal() {
    const modal = document.getElementById('evidence-modal');
    if (modal) modal.classList.add('active');
    loadEvidenceLogs();
}

function closeEvidenceModal() {
    const modal = document.getElementById('evidence-modal');
    if (modal) modal.classList.remove('active');
}

async function loadEvidenceLogs() {
    const tbody = document.getElementById('evidence-table-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/evidence');
        const logs = await res.json();

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No evidence recorded yet. Run a scan!</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td>#${l.id}</td>
                <td><strong>${l.application_number}</strong></td>
                <td><span class="badge-sub">${l.step_name}</span></td>
                <td><span class="font-bold text-${l.severity === 'SUCCESS' ? 'success' : (l.severity === 'WARNING' ? 'danger' : 'accent')}">${l.severity}</span></td>
                <td>${l.finding}</td>
                <td class="font-mono text-sm">${l.created_at}</td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger">Failed to load evidence: ${err.message}</td></tr>`;
    }
}
