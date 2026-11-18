# SSI Reference Data Validation & Exception Management System

A complete portfolio simulation of a controlled Standard Settlement Instruction (SSI) reference-data operation. It generates deterministic synthetic records, validates them against configurable rules, creates and prioritizes exceptions, demonstrates maker-checker workflow controls, records a structured audit trail, persists the result in SQLite, and produces analysis-ready CSV reports.

**Live project overview:** [prajuval69.github.io/ssi-reference-data-validation](https://prajuval69.github.io/ssi-reference-data-validation/)

> **Synthetic-data boundary:** every client, account, custodian, beneficiary, user, market, country and currency in this repository is invented. The project has no connection to a bank, custodian, production platform or real SSI dataset. Its rules and severity levels are demonstration conventions, not official banking policy.

## What works

- 250 deterministic SSI records with deliberate completeness, duplicate, reference, date, staleness, expiry and maker-checker defects
- eight separately persisted synthetic reference datasets
- 15 independent rules with a result for every record/rule pair
- one actionable exception per failed rule evaluation
- severity-first queue with filters for severity, status, client, market, currency, rule, age and assignee
- controlled `NEW → UNDER_REVIEW → REMEDIATION_REQUIRED/RESOLVED/REJECTED` workflow
- self-approval prevention and invalid-transition rejection
- audit events for creation, validation, exception creation, assignment, review, rejection and resolution
- SQLite tables, foreign keys, constraints and operational indexes
- 16 headline KPIs plus rule, currency, market, severity, status and source breakdowns
- 36 unit and integration tests

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[test]"
python -m ssi_validation.pipeline
pytest
```

The pipeline supports an alternate output root and record count (minimum 40):

```bash
python -m ssi_validation.pipeline --data-dir demo_data --records 500
```

## Pipeline

```text
Synthetic SSI + reference data
            ↓
     Input schema gate
            ↓
  15-rule validation engine
            ↓
 Validation results + exceptions
            ↓
 Assignment and maker-checker workflow
            ↓
   Audit trail + SQLite persistence
            ↓
 KPI and operational CSV reporting
```

## Project layout

```text
src/ssi_validation/       Python package
tests/                    pytest unit and integration suite
sql/                      reusable operational queries
data/raw/                 generated synthetic SSI input
data/reference/           generated reference tables
data/outputs/             generated reports
data/ssi_validation.db    generated SQLite database
docs/                     output interpretation guide
web/dist/                 static portfolio site
*.md                      business and technical specifications
```

## Generated reports

| File | Purpose |
|---|---|
| `validated_ssi.csv` | SSI records with `failed_rule_count` and `is_valid` |
| `validation_results.csv` | every record/rule PASS or FAIL result |
| `exceptions.csv` | prioritized exception queue with aging fields |
| `audit_log.csv` | structured action history |
| `kpi_summary.csv` | KPI value, unit and formula |
| `exception_summary.csv` | exception counts by operational dimension |

See [docs/sample_output_guide.md](docs/sample_output_guide.md) for interpretation and reconciliation checks.

## Design choices

- `record_id` is the physical primary key; `ssi_id` is intentionally not unique so duplicate identifiers can be ingested and detected rather than rejected before validation.
- Raw invalid values are accepted into the staging-style `ssi_records` table. Reference integrity is assessed by the rule engine, while relational foreign keys protect result, exception and audit relationships.
- Business time is fixed in configuration, making data, validation results, workflow events, KPIs and CSV outputs reproducible.
- The queue ordering—Critical, High, Medium, Low; unresolved before terminal; oldest first—is a project convention.

## Useful commands

```bash
python -m ssi_validation.pipeline
pytest
python -m pytest tests/test_validation_rules.py
```

Operational SQL examples are in [sql/operational_queries.sql](sql/operational_queries.sql). Configuration lives in [src/ssi_validation/config.py](src/ssi_validation/config.py).
