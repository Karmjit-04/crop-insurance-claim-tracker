# 🌾 PMFBY Crop Insurance Claim Tracker (Agentic AI Hackathon 2026)

A beginner-friendly, 100% offline Agentic AI claim tracking and validation platform for Indian farmers, built with **Python 3.14**, **Flask**, **SQLite**, **Playwright**, and accessible **HTML5 / CSS3 / JavaScript**.

Designed specifically for the **Agentic AI Hackathon 2026**, this project includes a local mock insurance registry, automated Playwright browser inspection, a Human-in-the-Loop (HITL) safety gate, and full automated test verification for all four official hackathon test cases.

---

## 🌟 Features & Highlights

1. **Local Mock Crop Insurance Portal**:
   - Emulates the national PMFBY portal with synthetic farmer claim records.
   - Provides live DOM hooks (`#dom-claim-status`, `#dom-missing-doc`, `#dom-payment-status`, `#dom-season`, etc.) for Playwright automation.
2. **किसान-अनुकूल केवल हिन्दी डैशबोर्ड (Farmer-Friendly Hindi Dashboard)**:
   - Displays Application Number (आवेदन संख्या), Farmer Name (किसान का नाम), Crop (फसल), Season (मौसम), Claim Status (दावे की स्थिति), Missing Land Documents (अनुपलब्ध भूमि दस्तावेज), and Payment Disbursal Status (भुगतान की स्थिति).
   - High-contrast, color-coded accessibility indicators.
   - Dedicated exclusively to authentic Hindi terminology (खसरा-खतौनी, दावा स्वीकृत, अधिकार अभिलेख, आदि).
3. **Four Official Hackathon Test Cases**:
   - **TC1**: Read current claim status in the farmer's chosen language without distortion.
   - **TC2**: Accurately identify the exact missing land document (e.g. *Record of Rights / Khasra-Khatauni* for survey numbers).
   - **TC3**: Detect an agronomic season mismatch (e.g., Wheat sown in November cannot be Kharif) and propose a correction.
   - **TC4**: Strictly enforce that an approved claim is **never reported as paid** until bank credit confirmation is verified.
4. **Playwright Agentic Browser Automation**:
   - Automates DOM extraction, status monitoring, and form interaction.
5. **Human-in-the-Loop (HITL) Safety Gate**:
   - Strictly blocks the agent from modifying a season or uploading documents until explicit human approval is stored in SQLite.
6. **Re-Read Verification**:
   - Re-inspects the portal after an action to confirm whether it `SUCCESS`, `FAILED`, or remains `PENDING`.
7. **Audit Trail in SQLite**:
   - Persists synthetic claims, evidence logs, human approval actions, and test execution results.
8. **100% Offline & Free**:
   - Zero paid APIs, no Browserbase, no cloud subscriptions, and no payment cards needed.

---

## 🏗️ Architecture

```
                                    +-----------------------------+
                                    |     Farmer Dashboard        |
                                    | (Hindi, Punjabi, En, etc.)  |
                                    +--------------+--------------+
                                                   |
                       +---------------------------+---------------------------+
                       |                                                       |
                       v                                                       v
        +-----------------------------+                         +-----------------------------+
        |   Mock PMFBY Portal (Web)   |                         |  HITL Approvals Center      |
        |  /portal/claim/<app_no>     |                         |  /approvals                 |
        +--------------+--------------+                         +--------------+--------------+
                       ^                                                       |
        Playwright DOM | Form Submit                                           | Explicit
        Inspection     | Post-Approval                                         | Consent
                       |                                                       v
        +--------------+-------------------------------------------------------+--------------+
        |                                                                                     |
        |                       Agentic Runner & Inspector (agent/)                           |
        |        - TC1: Multilingual parser      - TC3: Season mismatch & HITL proposal       |
        |        - TC2: Missing land doc locator - TC4: Disbursal invariant enforcement       |
        |                                                                                     |
        +--------------------------------------+----------------------------------------------+
                                               |
                                               v
                                +-----------------------------+
                                |      SQLite Database        |
                                |  (claims, evidence_logs,    |
                                |   approval_requests, tests) |
                                +-----------------------------+
```

---

## 💻 Windows 11 Setup Instructions

### 1. Prerequisites
- **Windows 11** (64-bit)
- **Python 3.10+** (Python 3.14 recommended)

Verify Python from Windows PowerShell or Command Prompt:
```powershell
python --version
```

### 2. Clone and open the project
```powershell
git clone https://github.com/<your-username>/crop-insurance-claim-tracker.git
cd crop-insurance-claim-tracker
```

### 3. Install Dependencies
Install Flask, Playwright, and Pytest:
```powershell
python -m pip install -r requirements.txt
```

The Playwright driver (`app/agent/pw_agent.js`) runs under Node. Install the package once in the repo root:
```powershell
npm install playwright
```

Install Playwright's local Chromium browser binary:
```powershell
python -m playwright install chromium
```

---

## 🚀 Running the Application

### Start the Local Web Server
Run:
```powershell
cd app
python app.py
```

Open your browser to:
- **Farmer Dashboard**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Human Approval Center**: [http://127.0.0.1:5000/approvals](http://127.0.0.1:5000/approvals)
- **Official Test Execution Center**: [http://127.0.0.1:5000/tests](http://127.0.0.1:5000/tests)
- **Sample Mock Insurance Portal Dossier**: [http://127.0.0.1:5000/portal/claim/CROP-2026-TC1](http://127.0.0.1:5000/portal/claim/CROP-2026-TC1)

---

## 🧪 Running the Official Test Suite

### Method 1: Command-Line Test Runner
Run the standalone runner with complete summary output:
```powershell
cd app
python run_tests.py
```

### Method 2: Running with Pytest
From the repo root:
```powershell
python -m pytest -v tests/test_official_cases.py
```

### Method 3: In-Browser GUI Test Runner
Navigate to [http://127.0.0.1:5000/tests](http://127.0.0.1:5000/tests) and click **"Run All 4 Official Test Cases Now"**. The results will run live and record execution timestamps directly into SQLite.

---

## 📋 Hackathon Test Cases Detailed Breakdown

| Test ID | Requirement | Synthetic Claim Target | Verification Logic |
| :--- | :--- | :--- | :--- |
| **TC1** | Hindi claim status reading | `CROP-2026-TC1` | Reads claim status and bank status in farmer's Hindi language (`दावा समिति द्वारा स्वीकृत`, `भुगतान पूर्ण - किसान के बैंक खाते में जमा`) without translation distortion. |
| **TC2** | Identify exact missing land document | `CROP-2026-TC2` | Inspects DOM and identifies that Survey `SURV-208/B` lacks the `Record of Rights (RoR / Khasra-Khatauni)`. |
| **TC3** | Detect incorrect season & enforce HITL | `CROP-2026-TC3` | Identifies that Wheat sown on `2025-11-15` cannot be Kharif; proposes `Rabi 2025-26`; blocks automated change until human approval is stored in SQLite. |
| **TC4** | Disbursal Safety Invariant | `CROP-2026-TC4` | Claim has `APPROVED` status, but payment is `UNDER_BANK_PROCESSING`. Agent strictly reports `Approved - Pending Bank Credit Confirmation`, **never reporting as paid**. |

---

## 🗄️ Database Schema (`crop_tracker.db`)

- `claims`: Application number, farmer details, crop, season, sowing date, survey number, claim status, missing doc, payment status, amounts, bank reference.
- `evidence_logs`: Audit trail of DOM extractions, validation findings, severity levels, and raw evidence.
- `approval_requests`: Human-in-the-loop queue containing proposed values, previous values, reasons, and approval/rejection state.
- `test_results`: Execution history, pass/fail status, duration in seconds, and detail logs.
