# MASTER PROMPT — SSI Reference Data Validation & Exception Management System

## Objective

Build a complete, production-quality, resume-ready portfolio project called:

**SSI Reference Data Validation & Exception Management System**

The project simulates a controlled Standard Settlement Instruction (SSI) reference-data operation using synthetic data.

The system must ingest SSI records, validate them against configurable business rules, identify and classify exceptions, create an operational exception queue, support maker-checker workflow concepts, maintain a complete audit trail, calculate operational KPIs, persist data in SQLite, and expose clean outputs for analysis/reporting.

This is a portfolio simulation only. Use synthetic data and clearly state that no real bank, client, custodian, settlement, or production-system data is used.

---

## First Step — Inspect the Workspace

Before implementing anything:

1. Inspect the complete workspace.
2. Read every `.md` file supplied with this project.
3. Treat this file and the supporting specifications as the source of truth.
4. Identify existing files before creating new ones.
5. Reuse useful existing code where appropriate.
6. Do not delete unrelated user files.

Do not stop at scaffolding.

---

## Required Technology

Prefer a simple, maintainable stack:

- Python 3.11+
- Pandas
- NumPy
- SQLite
- SQL
- pytest
- Standard Python libraries where possible

Optional:
- Pydantic for schema validation
- Typer/Click only if a CLI materially improves usability

Do not introduce unnecessary frameworks.

---

## Core Functional Requirements

### 1. Synthetic Data Generation

Create a deterministic synthetic SSI dataset containing realistic operational edge cases.

Include fields such as:

- ssi_id
- client_id
- client_name
- market
- country
- currency
- account_number
- custodian
- beneficiary_name
- settlement_method
- source_channel
- effective_date
- expiry_date
- status
- maker
- checker
- created_at
- updated_at

Generate enough records to make the project meaningful.

The generator must intentionally produce both valid records and invalid/problematic records.

Use a fixed random seed.

Do not use real financial institution or customer information.

---

## 2. Reference Data

Create synthetic reference tables for:

- supported currencies
- markets
- countries
- settlement methods
- source channels
- valid status values
- allowed currency/country relationships where appropriate
- allowed workflow transitions

Reference data must be stored separately from transactional SSI data.

---

## 3. Validation Engine

Build a modular validation engine.

Each validation rule must have:

- rule_id
- rule_name
- description
- severity
- validation function
- result
- exception reason

At minimum implement:

### Completeness
Detect missing mandatory fields.

### Duplicate SSI
Detect duplicate SSI identifiers.

### Duplicate Business Instruction
Detect conflicting/duplicate active instructions using a configurable business key such as:

client + market + currency + settlement method.

### Currency Validation
Check whether the currency exists in the supported-currency reference data.

### Account Format
Validate synthetic account-number format.

### Settlement Method
Check against supported settlement methods.

### Source Validation
Check whether the source channel is authorized.

### Date Consistency
Detect:

- expiry before effective date
- missing effective date
- invalid date values

### Stale Record
Identify records that have not been updated within a configurable threshold.

### Expired Instruction
Identify instructions whose expiry date has passed.

### Currency/Country Consistency
Where reference data supports the rule, identify incompatible combinations.

### Maker-Checker
Detect:

- missing checker
- missing maker
- maker equals checker

### Status Validation
Ensure status belongs to the allowed status set.

### Active Conflict
Detect multiple active instructions for the same business key where only one should be active.

---

## 4. Rule Configuration

Do not scatter business rules throughout the code.

Create a central configuration layer containing values such as:

- stale_days
- supported currencies
- account regex
- severity mapping
- allowed statuses
- allowed transitions
- cutoff/reference dates where needed

Rules should be easy to modify without rewriting the validation engine.

---

## 5. Exception Classification

Each failed validation must create an exception.

Classify exceptions into:

- Critical
- High
- Medium
- Low

The severity mapping must be explicit and documented.

Do not describe these levels as official banking policy.

Each exception should contain:

- exception_id
- ssi_id
- rule_id
- severity
- exception_type
- description
- detected_at
- status
- assigned_to
- resolution_notes
- resolved_at

---

## 6. Exception Queue

Build a queryable operational exception queue.

It must support filtering by:

- severity
- status
- client
- market
- currency
- rule
- age
- assignee

Default sorting should prioritize operational risk, for example:

1. Critical
2. High
3. Medium
4. Low

Then older unresolved exceptions first.

Do not call this an official bank prioritization policy; document it as a project rule.

---

## 7. Maker-Checker Workflow

Implement workflow concepts:

NEW
→ UNDER_REVIEW
→ REMEDIATION_REQUIRED
→ RESOLVED

Alternative terminal state:

REJECTED

Rules:

- maker creates/modifies an SSI
- checker reviews the change
- maker cannot approve their own change
- invalid status transitions are rejected
- every transition generates an audit event

The workflow must be testable.

---

## 8. Audit Trail

Every important system action must be recorded.

Audit fields should include:

- audit_id
- entity_type
- entity_id
- action
- old_value/state
- new_value/state
- performed_by
- performed_at
- reason

The audit trail should cover:

- validation
- exception creation
- assignment
- status transitions
- approval/rejection
- resolution

Where practical, preserve old/new state as structured JSON.

---

## 9. Database

Use SQLite.

Create a clean schema with tables for at least:

- ssi_records
- reference_currencies
- reference_markets
- reference_countries
- reference_settlement_methods
- validation_results
- exceptions
- audit_log

Use primary keys, foreign keys, indexes, and sensible constraints.

Add indexes for common operational queries such as:

- status
- severity
- currency
- market
- detected_at
- ssi_id

---

## 10. Processing Pipeline

Create an end-to-end pipeline:

Raw SSI Data
→ Schema Validation
→ Reference Data Checks
→ Rule Engine
→ Validation Results
→ Exception Classification
→ Exception Queue
→ Workflow/Audit Processing
→ KPI Calculation
→ Reporting Outputs

The pipeline should be runnable with one clear command.

---

## 11. KPIs

Calculate at least:

- total SSI records
- valid SSI records
- invalid SSI records
- validation pass rate
- exception count
- exception rate
- critical exception count
- high exception count
- unresolved exception count
- resolved exception count
- duplicate rate
- stale record count
- expired instruction count
- maker-checker violation count
- average exception age
- average remediation time
- exceptions by rule
- exceptions by currency
- exceptions by market
- exceptions by severity

Ensure formulas are documented.

---

## 12. Reporting Outputs

Generate clean outputs such as:

- `validated_ssi.csv`
- `validation_results.csv`
- `exceptions.csv`
- `audit_log.csv`
- `kpi_summary.csv`
- `exception_summary.csv`

If useful, also produce Excel-compatible files.

Do not generate unnecessary duplicate files.

---

## 13. Testing

Create comprehensive pytest coverage.

Test at minimum:

- mandatory-field validation
- duplicate detection
- business-key conflict detection
- currency validation
- account validation
- settlement-method validation
- source validation
- date validation
- stale detection
- expiry detection
- maker-checker restriction
- status transition rules
- severity classification
- exception creation
- KPI calculations
- audit-event creation
- deterministic data generation

Include boundary and negative cases.

---

## 14. Error Handling

The system must fail safely.

Examples:

- malformed input
- missing columns
- invalid dates
- duplicate identifiers
- database failures
- invalid workflow transitions
- unknown reference values

Errors should be informative without exposing secrets.

---

## 15. Documentation

Create:

- root README
- architecture documentation
- business rules documentation
- data dictionary
- database schema documentation
- workflow documentation
- testing documentation
- setup/run instructions
- sample output explanation

Documentation should be practical rather than excessively verbose.

---

## 16. Repository Quality

Do not include:

- `.env` secrets
- credentials
- API keys
- IDE-specific junk
- Python cache directories
- unnecessary generated files
- temporary files
- real personal/financial data

Include a useful `.gitignore`.

---

## 17. Final Verification

Before declaring completion:

1. Run the complete pipeline.
2. Run all tests.
3. Fix all failures.
4. Verify database creation.
5. Verify CSV outputs.
6. Verify KPI calculations.
7. Verify workflow constraints.
8. Verify audit records.
9. Confirm deterministic behavior.
10. Inspect repository cleanliness.
11. Confirm documentation matches implementation.
12. Confirm all data is synthetic.

Do not claim a feature exists unless it actually works.

## Final Deliverable

Deliver a clean repository that can be published as a public GitHub portfolio project and discussed confidently in an interview for reference-data, operations, data-quality, business-operations, or analytics roles.
