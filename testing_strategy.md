# Testing Strategy

## Unit Tests

Every important business rule should have focused unit tests.

## Integration Tests

Test:

- synthetic data generation
- database initialization
- end-to-end validation
- exception creation
- KPI calculation

## Edge Cases

Include tests for:

- empty input
- missing columns
- duplicate IDs
- invalid currency
- invalid account format
- expiry before effective date
- exact stale threshold
- maker equals checker
- invalid workflow transition
- no exceptions
- all records failing
- all records passing

## Determinism

Given the same random seed and configuration, synthetic data generation should produce reproducible results.

## Expected Outcome

The full test suite should pass before the project is considered complete.

## Implemented Coverage

The suite contains 36 tests across:

- `test_validation_rules.py`: all 15 rules, malformed schema, negative cases and stale-date boundary
- `test_synthetic_and_exceptions.py`: deterministic generation, deliberate defects and one-to-one failure/exception creation
- `test_workflow_database.py`: assignment, valid and invalid transitions, self-approval prevention, queue filters, audit events and foreign keys
- `test_kpis_pipeline.py`: KPI formulas plus database and output integration checks

Run `pytest` from the repository root. Tests use temporary directories and do not depend on committed generated data.
