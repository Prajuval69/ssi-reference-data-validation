# Database Schema

Use SQLite with normalized tables.

## Required Tables

### ssi_records
Stores SSI master/reference records.

### reference_currencies
Supported synthetic currencies.

### reference_markets
Supported synthetic markets.

### reference_countries
Synthetic country reference data.

### reference_settlement_methods
Allowed settlement methods.

### validation_results
Stores every rule evaluation.

### exceptions
Stores actionable validation failures.

### audit_log
Stores workflow and operational events.

Additional controlled tables store source channels, statuses, currency/country pairs and workflow transitions.

## Database Requirements

- Primary keys
- Foreign keys
- NOT NULL constraints where appropriate
- Unique constraints where appropriate
- Indexes for operational queries

Recommended indexes:

```text
ssi_records(status)
ssi_records(currency)
ssi_records(market)
validation_results(ssi_id)
validation_results(rule_id)
exceptions(status)
exceptions(severity)
exceptions(detected_at)
audit_log(entity_id)
```

## Physical-Key Decision

`ssi_records.record_id` is the primary key. `ssi_id` is indexed but deliberately not unique: duplicate business identifiers are a required input defect and must reach the validation engine. `validation_results.record_id` and `exceptions.record_id` are foreign keys back to the physical record.

Raw SSI reference columns do not have reference-table foreign keys because invalid values must be ingested and reported as exceptions. Controlled reference tables do enforce their own relationships. Foreign keys protect result and exception lineage.

The executable schema is defined in `src/ssi_validation/database.py`; reusable analyst queries are in `sql/operational_queries.sql`.
