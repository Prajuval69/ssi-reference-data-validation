# Exception Management Specification

## Exception Record

Each failed validation should produce an exception containing:

- unique exception ID
- SSI ID
- rule ID
- severity
- exception type
- human-readable description
- detected timestamp
- status
- assignee
- resolution notes
- resolved timestamp

## Queue Behavior

The queue should support filtering by:

- Critical/High/Medium/Low
- New/Under Review/Remediation Required/Resolved/Rejected
- client
- currency
- market
- rule
- age
- assignee

## Prioritization

Default ordering:

1. severity descending
2. unresolved before resolved
3. oldest unresolved first

This is a project-specific operational convention.

## Exception Aging

Calculate:

```text
current_time - detected_at
```

for unresolved exceptions.

Create useful aging buckets such as:

- 0–1 day
- 2–3 days
- 4–7 days
- 8–30 days
- 30+ days

## Query Interface

`ExceptionQueue.query(QueueFilters(...))` applies parameterized filters for all fields above. Results add `age_days` and `aging_bucket`, then sort by project severity rank, unresolved before terminal records, detection time and exception ID. Client filtering accepts either the synthetic client ID or exact synthetic client name.
