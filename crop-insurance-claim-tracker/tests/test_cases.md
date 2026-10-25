# Official Test Cases (TC1-TC4)

Automated in `tests/test_official_cases.py` and `app/run_tests.py`.
Synthetic data: `data/sample_claims.json` (seeded into SQLite by `app/database/db.py`).

| ID | Requirement | Claim | Expected result |
| :-- | :-- | :-- | :-- |
| TC1 | Read current claim status in the farmer's language (Hindi) | `CROP-2026-TC1` | Status shows "दावा समिति द्वारा स्वीकृत", payment shows "भुगतान पूर्ण - किसान के बैंक खाते में जमा", no missing documents. |
| TC2 | Identify the exact missing land document | `CROP-2026-TC2` | Missing document is `Record of Rights (RoR / Khasra-Khatauni)` for survey `SURV-208/B`. |
| TC3 | Detect an incorrect season and propose a correction | `CROP-2026-TC3` | Wheat sown 2025-11-15 is flagged as not Kharif; `Rabi 2025-26` proposed; portal change blocked until a human approval is stored in SQLite; re-read after the change shows no mismatch. |
| TC4 | Never report an approved claim as paid until bank credit is confirmed | `CROP-2026-TC4` | Claim is `APPROVED` + `UNDER_BANK_PROCESSING`; reported as "Approved - Pending Bank Credit Confirmation", `reported_as_paid = False`. |

## How to run

From the repo root:

```
python -m pytest -v tests/test_official_cases.py
```

Or from `app/`:

```
python run_tests.py
```
