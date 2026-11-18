# KPI Specification

## Core KPIs

### Total SSI Records
Count of unique SSI records processed.

### Valid SSI Records
Records with no failed validation rules.

### Invalid SSI Records
Records with at least one failed validation rule.

### Validation Pass Rate

```text
valid records / total records × 100
```

### Exception Rate

```text
exceptions / total SSI records × 100
```

### Critical Exception Count
Number of critical exceptions.

### Unresolved Exception Count
Exceptions not in a terminal resolved/rejected state.

### Duplicate Rate

```text
duplicate/conflicting records / total records × 100
```

### Stale Record Count
Number of records exceeding the configured stale threshold.

### Expired Instruction Count
Number of instructions past their expiry date.

### Maker-Checker Violation Count
Number of detected maker-checker violations.

### Average Exception Age
Average age of unresolved exceptions.

### Average Remediation Time
Average time between exception creation and resolution for resolved exceptions.

## Breakdown KPIs

Produce counts by:

- rule
- severity
- currency
- market
- status
- source channel

## Implementation Conventions

- Total records counts physical `record_id` values, including records with deliberately duplicated `ssi_id` values.
- Invalid records are distinct physical records with one or more failed rules.
- Exception rate may exceed 100% because one record can fail multiple rules.
- Duplicate rate uses the union of records failing `SSI-002` or `SSI-003`, avoiding double-counting.
- Unresolved excludes both terminal states: `RESOLVED` and `REJECTED`.
- Average exception age uses unresolved exceptions only.
- Average remediation time uses `detected_at` to `resolved_at` for `RESOLVED` exceptions only.

`kpi_summary.csv` includes the formula beside every value. `exception_summary.csv` stores dimensional counts in long form.
