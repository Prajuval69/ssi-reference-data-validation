# Business Rules

## Rule Catalog

| Rule ID | Rule | Default Severity |
|---|---|---|
| SSI-001 | Mandatory fields | High |
| SSI-002 | Duplicate SSI ID | Critical |
| SSI-003 | Duplicate/conflicting active instruction | Critical |
| SSI-004 | Unsupported currency | High |
| SSI-005 | Invalid account format | High |
| SSI-006 | Invalid settlement method | Medium |
| SSI-007 | Unauthorized source | High |
| SSI-008 | Invalid effective/expiry dates | High |
| SSI-009 | Stale instruction | Medium |
| SSI-010 | Expired instruction | High |
| SSI-011 | Currency/country inconsistency | Medium |
| SSI-012 | Missing maker/checker | High |
| SSI-013 | Maker equals checker | Critical |
| SSI-014 | Invalid workflow status | High |
| SSI-015 | Invalid market/country relationship | Medium |

Severity values are project-specific classifications for demonstration and are not official banking policy.

## Business Key

A configurable business key should identify potential conflicting active instructions. A suitable default is:

`client_id + market + currency + settlement_method`

## Stale Records

A record is stale when its last update is older than the configured `stale_days` threshold.

## Expired Records

An instruction is expired when the current business date is later than its expiry date.

## Maker-Checker

The user who creates or modifies an instruction cannot approve the same change.

## Workflow

```text
NEW
  ↓
UNDER_REVIEW
  ↓
REMEDIATION_REQUIRED
  ↓
UNDER_REVIEW
  ↓
RESOLVED

OR

REJECTED
```

Only configured transitions are permitted.

## Configuration Location

The executable rule catalog, severity mapping, stale threshold, account regex, active statuses, terminal statuses, business key, fixed business time and allowed transitions are centralized in `src/ssi_validation/config.py`. Validation functions consume this configuration rather than redefining thresholds or status lists.
