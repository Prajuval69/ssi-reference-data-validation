# Setup & Run

## Environment

Python 3.11+ recommended.

## Installation

Create a virtual environment and install the package plus test dependencies.

Example:

```bash
python -m venv .venv
```

Activate the environment and install:

```bash
python -m pip install -e ".[test]"
```

## Run

The implementation should provide one clear command for the full pipeline.

```bash
python -m ssi_validation.pipeline
```

Optional arguments:

```bash
python -m ssi_validation.pipeline --data-dir demo_data --records 500
```

`--records` must be at least 40 because the generator reserves deterministic positions for all edge cases.

## Tests

Run:

```bash
pytest
```

## Expected Outputs

The pipeline should generate:

- processed SSI records
- validation results
- exception queue
- audit log
- KPI summaries
- SQLite database

The default locations are `data/raw`, `data/reference`, `data/outputs`, and `data/ssi_validation.db`. Existing generated operational tables are cleared and rebuilt on every run, so reruns are idempotent.

If you prefer requirements-only installation, run `python -m pip install -r requirements.txt` and set `PYTHONPATH=src` before invoking the module.
