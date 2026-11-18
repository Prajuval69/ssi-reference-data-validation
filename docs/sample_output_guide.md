# Sample Output Guide

All outputs describe the deterministic synthetic run and must not be interpreted as bank or production data.

## Reconciliation

Use these checks after a run:

1. `validation_results.csv` contains `record count × 15` rows.
2. Every `FAIL` validation row has exactly one row in `exceptions.csv` with the same `record_id` and `rule_id`.
3. `validated_ssi.failed_rule_count` equals the number of failed validation rows for that physical record.
4. `valid_ssi_records + invalid_ssi_records = total_ssi_records`.
5. `exception_count` equals the row count of `exceptions.csv`.
6. SQLite table counts agree with their CSV counterparts.

## Reading the reports

- A duplicated `ssi_id` can appear on multiple physical `record_id` rows; this is deliberate.
- `is_valid` is true only when every configured rule passed.
- `exception_rate` counts failed rules per SSI and is not a percentage of unique defective records.
- `age_days` is calculated from the fixed configured business time, not the computer clock.
- A zero average exception age means exceptions were detected at the configured business time.
- Resolved and rejected exceptions remain in the output for audit and KPI history.

## SQLite analysis

Open `data/ssi_validation.db` with any SQLite-compatible tool. Start with the read-only examples in `sql/operational_queries.sql`.
