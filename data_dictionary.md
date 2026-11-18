# Data Dictionary

## SSI Records

| Field | Description |
|---|---|
| record_id | Physical integer primary key used to retain duplicate business identifiers |
| ssi_id | Unique SSI identifier |
| client_id | Synthetic client identifier |
| client_name | Synthetic client name |
| market | Market associated with the instruction |
| country | Country associated with the instruction |
| currency | Settlement currency |
| account_number | Synthetic settlement account |
| custodian | Synthetic custodian |
| beneficiary_name | Synthetic beneficiary |
| settlement_method | Settlement method |
| source_channel | Origin of instruction |
| effective_date | Instruction effective date |
| expiry_date | Instruction expiry date |
| status | Workflow status |
| maker | User who created/modified record |
| checker | Reviewer |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |

## Validation Results

Recommended fields:

- validation_id
- record_id
- ssi_id
- rule_id
- rule_name
- result
- severity
- exception_reason
- validated_at

## Exceptions

Recommended fields:

- exception_id
- record_id
- ssi_id
- rule_id
- severity
- exception_type
- description
- status
- assigned_to
- detected_at
- resolution_notes
- resolved_at

The exported queue also includes joined client, market and currency fields plus calculated `age_days` and `aging_bucket` values.

## Audit Log

Recommended fields:

- audit_id
- entity_type
- entity_id
- action
- old_state
- new_state
- performed_by
- performed_at
- reason

`old_state` and `new_state` contain JSON when a state snapshot is available.
