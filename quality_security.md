# Quality & Security Requirements

## Synthetic Data Only

Never use:

- real client names
- real account numbers
- real bank account details
- real custodian records
- credentials
- API keys
- private data

## Reproducibility

Use deterministic random seeds.

## Input Quality

Validate:

- required columns
- types
- date formats
- reference values
- nullability

## Security Hygiene

Never commit:

- `.env`
- credentials
- tokens
- private keys
- local secrets

## Repository Hygiene

Exclude:

- `__pycache__/`
- `.pytest_cache/`
- virtual environments
- IDE metadata
- temporary files
- large unnecessary generated artifacts

Use `.gitignore`.
