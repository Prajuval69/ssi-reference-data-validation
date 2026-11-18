# Audit & Controls

## Audit Events

Record events for:

- SSI creation
- SSI modification
- validation execution
- exception creation
- exception assignment
- status changes
- approval
- rejection
- remediation
- resolution

## Audit Record

Each event should contain:

- audit_id
- entity_type
- entity_id
- action
- actor
- timestamp
- old_state
- new_state
- reason

## Control Objectives

The simulation should demonstrate:

- traceability
- segregation of maker/checker responsibilities
- controlled workflow transitions
- validation before downstream use
- exception visibility
- reproducibility
- auditability

Do not represent these as evidence of compliance with a specific regulation or financial institution's control framework.

## Implementation

Old and new state are JSON strings so state changes remain machine-readable. Audit IDs are deterministic sequential identifiers within a rebuilt database. The standard pipeline records SSI creation, validation completion, exception creation, assignment, review transitions, remediation, approval/resolution and rejection. Audit events and their related state updates share the same SQLite connection and commit boundary.
