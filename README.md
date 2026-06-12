# CarbonRadar SME

CarbonRadar SME is a local Python data pipeline for Taiwanese SME manufacturers. It turns sample electricity bills, fuel logs, and supplier disclosure questionnaire data into Scope 1 and Scope 2 emissions estimates, Taiwan carbon-fee scenarios, readiness scores, and Markdown reports.

This repository is a university Big Data Systems final project foundation. It is intentionally simple, reproducible, and explainable.

## Target Customer

The target users are Taiwanese SME manufacturers with roughly 20-200 employees, especially metal processing, CNC machining, plastic injection, and electronics component suppliers. The typical operator is a factory owner, plant manager, QA or ISO contact, ESG coordinator, finance admin, or procurement staff member who needs to answer customer carbon questionnaires.

## MVP Scope

v0.2 includes:

- deterministic sample organization, electricity, fuel, supplier disclosure, and emission factor CSVs
- curated public demand evidence CSVs
- CSV ingestion
- validation and month normalization
- Scope 1 and Scope 2 emissions calculations
- Taiwan carbon-fee scenario simulation
- supplier disclosure readiness scoring
- Markdown report generation
- demand evidence validation and scoring
- CLI commands
- pytest coverage

v0.2 does not include a frontend, OCR, live APIs, scraping, full Scope 3, product carbon footprinting, deployment infrastructure, ISO certification workflow, or legal interpretation.

## Data Pipeline Overview

1. Load sample CSV files from `data/sample/`.
2. Validate activity records and normalize months to `YYYY-MM`.
3. Preserve rejected-row reasons in `data/outputs/validation_report.csv`.
4. Calculate Scope 1 fuel and Scope 2 electricity emissions.
5. Preserve row-level calculation traceability in `data/outputs/emissions_trace_{org}_{year}.csv`.
6. Calculate annual totals and carbon-fee scenarios.
7. Score supplier disclosure readiness.
8. Generate one Markdown report per organization-year in `data/outputs/`.

The v0.2 demand evidence workflow separately loads curated CSV files from `data/demand_evidence/`, validates source metadata, scores market signals, and generates `data/outputs/demand_evidence_summary.md`.

## Quickstart

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m carbonradar.cli run-demo --org ORG001 --year 2025
```

The demo command writes outputs to `data/outputs/`, including:

- `validation_report.csv`
- `emissions_trace_ORG001_2025.csv`
- `monthly_emissions_ORG001_2025.csv`
- `annual_emissions_ORG001_2025.csv`
- `fee_scenarios_ORG001_2025.csv`
- `readiness_ORG001_2025.csv`
- `ORG001_2025_carbonradar_report.md`

## Sample Commands

```bash
python -m carbonradar.cli ingest-sample
python -m carbonradar.cli validate
python -m carbonradar.cli validate-bad-demo
python -m carbonradar.cli validate-demand-evidence
python -m carbonradar.cli build-demand-report
python -m carbonradar.cli calc-emissions --org ORG001 --year 2025
python -m carbonradar.cli score-readiness --org ORG001 --year 2025
python -m carbonradar.cli build-report --org ORG001 --year 2025
python -m carbonradar.cli run-demo --org ORG001 --year 2025
```

## Data Sources And Assumptions

Sample data is synthetic and deterministic:

- `ORG001`: metal processing / fastener factory, two sites
- `ORG002`: CNC machining factory, one site
- `ORG003`: plastic injection factory, one site

The demo electricity factor is `0.467 kgCO2e/kWh` for 2025. Diesel and natural gas factors are demo placeholders and are clearly marked in `data/sample/emission_factors.csv` and generated reports.

## Demand Evidence Pipeline

v0.2 adds a reproducible demand evidence workflow for the final project requirement "Evidence of Demand and Willingness to Pay." It uses curated public-data seed CSVs instead of interviews, scraping, or live APIs.

Evidence categories:

- official regulatory sources
- market-size sources
- competitor pricing benchmarks
- ESG job posting examples
- public procurement examples
- willingness-to-pay assumptions

Run:

```bash
python -m carbonradar.cli validate-demand-evidence
python -m carbonradar.cli build-demand-report
```

Outputs:

- `data/outputs/demand_evidence_validation_report.csv`
- `data/outputs/demand_signal_scores.csv`
- `data/outputs/demand_evidence_summary.md`

Each evidence row includes source name, source URL, access date, notes, and confidence level. Rows marked `needs_verification` are treated as weak signals. Willingness-to-pay rows are pricing hypotheses and are not presented as verified market facts.

The demand score measures public-data support for the demand hypothesis. It does not verify customer demand or willingness to pay. Interviews or pilots are recommended future validation steps.

Carbon-fee scenarios use:

- threshold: `25,000 tCO2e`
- standard rate: `NT$300/tCO2e`
- preferential A rate: `NT$50/tCO2e`
- preferential B rate: `NT$100/tCO2e`

The v0.1.1 demo scenario tracks:

- `is_subject_to_fee`: annual emissions are greater than or equal to `25,000 tCO2e`
- `remaining_to_threshold_tco2e`: `max(25,000 - annual emissions, 0)`
- `excess_over_threshold_tco2e`: `max(annual emissions - 25,000, 0)`

The v0.2.1 demo estimates chargeable emissions with a simplified K-value model:

- `k_value_tco2e`: default `25,000 tCO2e`
- `adjustment_factor`: default `1.0`
- `chargeable_emissions_tco2e`: `max(annual emissions - k value, 0) x adjustment factor` when subject to fee, otherwise `0`

Scenario fees are calculated from chargeable emissions after the simplified K-value step. This is a simplified planning model, not a legal interpretation of the official fee base.

## Validation Bad-Data Demo

The clean sample pipeline is not contaminated with invalid rows. To demonstrate validation behavior, run:

```bash
python -m carbonradar.cli validate-bad-demo
```

This writes `data/outputs/validation_bad_demo_report.csv` and demonstrates negative kWh, missing `org_id`, invalid month, negative fuel quantity, and electricity outlier warning handling.

## Traceability

Emissions trace outputs include `source_document`, `source_dataset`, and `source_row_number` so each calculated emissions row can be traced back to a synthetic bill or fuel log record.

## Readiness Scoring

When validated activity data is available, readiness scoring uses actual electricity month coverage, fuel record coverage, source-document coverage, and emission-factor metadata completeness. When only questionnaire data is provided, it falls back to the supplier disclosure proxy fields.

## Limitations

- Fuel emission factors are placeholders for demo use.
- Scope 3 is not implemented.
- Reports are Markdown only; PDF rendering is out of scope.
- The project does not connect to government APIs or utility systems.
- The demand evidence pipeline does not scrape websites or refresh dynamic sources automatically.
- The project does not provide ISO 14064 verification, legal advice, tax advice, or certification advice.

## Legal And Privacy Disclaimer

This project is for education, internal pre-audit planning, and supplier disclosure preparation. Outputs are scenario estimates only. Replace demo data and placeholder factors with verified sources before any real customer, regulatory, tax, certification, or public reporting use.

The sample data is synthetic and does not contain personal data or confidential business records.

## Future Roadmap

- Replace placeholder fuel factors with verified factor sources.
- Add user-provided CSV import templates.
- Add richer validation reports and source-document tracking.
- Add PDF report export.
- Add optional dashboard after the local pipeline is stable.
- Explore OCR and live API ingestion in later phases only.
