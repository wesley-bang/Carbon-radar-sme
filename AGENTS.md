# AGENTS.md

## Project

This repository is `Carbon-radar-sme`.

CarbonRadar SME is a Big Data Systems final project that demonstrates an end-to-end data product for Taiwanese SME manufacturers. The system estimates Scope 1 and Scope 2 emissions from electricity and fuel activity data, simulates Taiwan carbon-fee scenarios, scores supplier disclosure readiness, and generates reports.

## Current phase

We are building v0.1 foundation only.

Do not build a frontend yet.
Do not implement OCR yet.
Do not connect to live government APIs yet.
Do not implement full Scope 3 or product carbon footprint calculation.
Do not over-engineer with Kafka, Spark, Airflow, or Kubernetes.

Focus on a clean, reproducible local data pipeline.

## Engineering goals

The repository should demonstrate:

1. Data ingestion from sample CSV files.
2. Data validation and normalization.
3. Scope 1 and Scope 2 emissions calculation.
4. Taiwan carbon-fee scenario simulation.
5. Supplier disclosure readiness scoring.
6. Markdown report generation.
7. CLI commands for running each step.
8. Unit tests with pytest.
9. Clear README and documentation.

## Tech stack

Use:

- Python 3.11+
- pandas
- pydantic
- pytest
- typer or argparse for CLI
- markdown output for reports

Avoid unnecessary dependencies.

## Coding standards

- Use type hints.
- Use deterministic sample data.
- Keep functions testable and small.
- Do not silently drop invalid rows.
- Every rejected row must include a reason.
- Preserve calculation traceability:
  - source row
  - activity type
  - amount
  - unit
  - emission factor ID
  - emission factor year
  - result in tCO2e

## Domain assumptions

Taiwan carbon-fee scenario assumptions for v0.1:

- threshold: 25,000 tCO2e per year
- standard rate: NT$300 / tCO2e
- preferential rate A: NT$50 / tCO2e
- preferential rate B: NT$100 / tCO2e

This is a scenario estimate, not a legal or tax determination.

For electricity, use demo factor:

- year: 2025
- activity_type: electricity
- unit: kWh
- kgco2e_per_unit: 0.467

For diesel and natural gas, use clearly marked placeholder factors and label them as demo placeholders.

## Acceptance criteria

The following command must work:

```bash
python -m carbonradar.cli run-demo --org ORG001 --year 2025