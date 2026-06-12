# Foundation Prompt

Implement CarbonRadar SME v0.1 as a reproducible local Python pipeline.

Constraints:

- no frontend
- no OCR
- no live APIs
- no full Scope 3
- no unnecessary infrastructure

Required capabilities:

- deterministic sample CSV data for three Taiwanese SME manufacturers
- validation and month normalization
- Scope 1 and Scope 2 emissions calculations with traceability
- Taiwan carbon-fee scenario simulation
- supplier disclosure readiness score
- Markdown organization-year reports
- command line workflow
- pytest coverage

Acceptance commands:

```bash
python -m pytest
python -m carbonradar.cli run-demo --org ORG001 --year 2025
```

