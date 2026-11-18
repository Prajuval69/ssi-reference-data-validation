# Workflow & Maker-Checker Specification

## SSI Workflow

Supported states:

- NEW
- UNDER_REVIEW
- REMEDIATION_REQUIRED
- RESOLVED
- REJECTED

## Valid Transitions

```text
NEW → UNDER_REVIEW
UNDER_REVIEW → REMEDIATION_REQUIRED
UNDER_REVIEW → RESOLVED
UNDER_REVIEW → REJECTED
REMEDIATION_REQUIRED → UNDER_REVIEW
```

No other transitions should be accepted unless explicitly configured.

## Maker-Checker Rule

The maker cannot be the checker for the same change.

The system must reject:

```text
maker == checker
```

## Audit Requirement

Every state transition must generate an audit event containing:

- entity
- previous state
- new state
- actor
- timestamp
- reason

## Exception Workflow

Exceptions may use:

```text
NEW
UNDER_REVIEW
REMEDIATION_REQUIRED
RESOLVED
REJECTED
```

Unresolved exceptions should remain visible in the operational queue.

## Implementation Notes

`WorkflowManager` checks every transition against central configuration. Moving an SSI or exception to `RESOLVED` or `REJECTED` requires an actor different from the underlying SSI maker. Blank assignees, unknown entities and skipped states raise `WorkflowError` without changing stored state.

The demonstration pipeline assigns every exception, begins review on eight, resolves three, sends two for remediation, rejects one and leaves two under review. These actions exist to populate realistic audit and remediation KPIs; they are not a recommended production operating model.
