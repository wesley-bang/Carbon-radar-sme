# CarbonRadar for Taiwanese SMEs
## What this project does
Estimate Scope 1/2 emissions for Taiwanese SME manufacturers,
simulate carbon-fee exposure, score supplier disclosure readiness,
and generate audit-friendly reports.
## Why this matters
- Taiwan carbon fee and inventory rules
- Listed-company supply-chain pressure
- SME pain point: scattered bills, no ESG headcount
## Target users
- 20–200 employee manufacturers
- Metal / plastic injection / CNC / electronics component suppliers
## System overview
13
- Data sources
- Architecture diagram
- Data model
- Calculation assumptions
## Quickstart
- Install
- Configure env
- Load sample data
- Run ETL
- Generate report
## Sample data
- utility_bills.csv
- fuel_logs.csv
- supplier_disclosure.csv
- synthetic bill PDFs
## CLI commands
- ingest
- normalize
- calc-emissions
- score-readiness
- build-report
## API examples
- POST /ingest/bills
- POST /calc/scope12
- POST /reports/annual
## Validation and tests
- unit tests
- golden snapshot tests
- OCR confidence threshold tests
## Legal and privacy notes
- PDPA-safe defaults
- document redaction
- retention policy
- cross-border processing checklist
## Limitations
- Scope 3 is not full LCA
- OCR still requires human review
- tariff interpretation may vary by user contract
