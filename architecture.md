# Architecture

## Components

### Data Generator
Creates deterministic synthetic SSI records and reference data.

### Ingestion Layer
Loads CSV/structured input and validates the expected schema.

### Reference Data Layer
Provides controlled lists and relationships used by validation rules.

### Validation Engine
Executes independent validation rules against each SSI.

### Exception Manager
Converts failed validation results into actionable exceptions.

### Workflow Manager
Controls maker-checker and exception status transitions.

### Audit Manager
Records important actions and state changes.

### KPI Engine
Aggregates validation and exception data into operational metrics.

### Persistence Layer
Stores records and results in SQLite.

## Implemented Modules

| Module | Responsibility |
|---|---|
| `config.py` | fixed business time, rule catalog, severities, business key and transitions |
| `references.py` | separate synthetic controlled lists and relationships |
| `synthetic.py` | reproducible valid and deliberately invalid SSI input |
| `validation.py` | schema gate and independent rule functions |
| `exceptions.py` | exception creation, aging buckets, safe filtered queue |
| `workflow.py` | assignment, transitions, self-approval control and audit calls |
| `database.py` | schema initialization and transactional persistence helpers |
| `audit.py` | deterministic structured audit events |
| `kpis.py` | headline and dimensional KPI datasets |
| `pipeline.py` | end-to-end orchestration and reporting |

`record_id` is a physical surrogate key. `ssi_id` remains non-unique at ingestion so the duplicate-ID rule can identify every affected row. Invalid raw reference values are likewise staged and flagged by validation instead of being blocked before evidence can be recorded.

## Design Principles

- modular
- deterministic
- testable
- auditable
- configuration-driven
- synthetic-data only
- minimal dependencies
