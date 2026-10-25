# Agent Workflow

1. **Inspect** - `PortalAgentRunner.inspect_claim_portal()` opens the local mock portal (`/portal/claim/<app_no>`) with Playwright (`app/agent/pw_agent.js`) and reads the live DOM (`#dom-claim-status`, `#dom-missing-doc`, `#dom-season`, ...). If the server is not running it falls back to the SQLite record.
2. **Validate** - `app/agent/inspector.py` runs four checks and writes each finding to `evidence_logs`:
   - TC1: render claim and payment status in Hindi (`agent/i18n.py`)
   - TC2: identify the exact missing land document
   - TC3: compare crop + sowing month with the declared season and propose a correction
   - TC4: enforce "approved is not paid" until bank credit and UTR are confirmed
3. **Propose** - when a change is needed (season correction or document upload) an `approval_requests` row is created with status `PENDING`.
4. **Human approval (HITL gate)** - a person approves or rejects on `/approvals`. `execute_season_correction()` and `execute_document_upload()` refuse to run unless an `APPROVED` request exists in SQLite.
5. **Act** - after approval, Playwright fills and submits the portal form.
6. **Re-read and verify** - the portal is read again and the result is reported as `SUCCESS`, `FAILED` or `PENDING` and logged to `evidence_logs`.

```
Inspect -> Validate (TC1-TC4) -> Propose -> Human approval -> Act (Playwright) -> Re-read -> SUCCESS / FAILED / PENDING
```
