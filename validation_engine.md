# Validation Engine Specification

## Design

Implement validations as independent, testable rules.

A rule should conceptually return:

```text
RuleResult(
    rule_id,
    ssi_id,
    passed,
    severity,
    reason
)
```

## Required Rule Categories

### Field Rules
- required fields
- data types
- valid formats

### Reference Rules
- supported currency
- supported settlement method
- valid source
- valid market/country

### Temporal Rules
- effective date
- expiry date
- stale records

### Uniqueness Rules
- duplicate SSI ID
- conflicting active instruction

### Control Rules
- maker/checker
- status

## Rule Execution

The engine should:

1. Receive normalized SSI data.
2. Load reference data.
3. Execute all applicable rules.
4. Store every rule result.
5. Create exceptions for failures.
6. Assign severity.
7. Return a structured validation summary.

Rules should not directly modify unrelated database tables.

## Implementation

`ValidationEngine.run()` first enforces the required column contract, then prepares dataset-level duplicate and business-key conflict sets. It evaluates all 15 functions for every physical record and emits a PASS or FAIL row each time. Rules return data only; exception creation and persistence are separate stages.

Invalid date text is coerced to an invalid timestamp and reported by `SSI-008`. An absent optional expiry date is allowed by date ordering and expiry checks, while a missing effective date fails both the mandatory and date-consistency controls. Exactly the configured stale threshold passes; a value older by any amount fails.
