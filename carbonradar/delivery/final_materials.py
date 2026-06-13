"""Generate source materials for the final English project report."""

from __future__ import annotations

from pathlib import Path

from carbonradar.delivery.dashboard_data import prepare_dashboard_data
from carbonradar.ingestion.load_sample import OUTPUT_DIR, PROJECT_ROOT


MATERIAL_FILENAMES = {
    "executive_summary": "executive_summary.md",
    "technical_system_summary": "technical_system_summary.md",
    "demand_evidence_digest": "demand_evidence_digest.md",
    "business_model_summary": "business_model_summary.md",
    "go_to_market_risks": "go_to_market_risks.md",
    "limitations_and_future_work": "limitations_and_future_work.md",
    "artifact_inventory": "artifact_inventory.md",
    "final_report_outline": "final_report_outline.md",
}


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def _bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _money(value: float) -> str:
    return f"NT${value:,.0f}"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sub_score_lines(sub_scores: dict[str, float]) -> str:
    labels = {
        "regulatory_pressure_score": "Regulatory pressure",
        "market_size_score": "Market size",
        "willingness_to_pay_score": "Willingness-to-pay hypotheses",
        "competitor_benchmark_score": "Competitor benchmark",
        "hiring_or_procurement_signal_score": "Hiring or procurement signal",
    }
    return "\n".join(f"- {labels.get(key, key)}: {value:.1f}" for key, value in sub_scores.items())


def _artifact_inventory(artifact_paths: dict[str, Path]) -> str:
    purposes = {
        "validation_report": "Validation issues from the clean sample activity data.",
        "emissions_trace": "Row-level Scope 1 and Scope 2 calculation trace with source references.",
        "monthly_emissions": "Monthly emissions summary by scope.",
        "annual_emissions": "Annual emissions summary by scope.",
        "fee_scenarios": "Simplified K-value carbon-fee scenario output.",
        "readiness": "Supplier disclosure readiness score output.",
        "markdown_report": "Organization-year Markdown report.",
        "html_report": "Standalone browser-ready HTML report for print-to-PDF.",
        "demand_evidence_validation_report": "Validation issues for curated demand evidence sources.",
        "demand_signal_scores": "Public-data support score and sub-scores.",
        "demand_evidence_summary": "Markdown digest of demand evidence and limitations.",
    }

    lines = [
        "# Artifact Inventory",
        "",
        "Generated artifacts from the reproducible local demo bundle.",
        "",
        "| Artifact | Path | Purpose | Exists |",
        "| --- | --- | --- | --- |",
    ]
    for name, path in artifact_paths.items():
        purpose = purposes.get(name, "Generated project artifact.")
        exists = "yes" if path.exists() else "no"
        lines.append(f"| {name} | `{_display_path(path)}` | {purpose} | {exists} |")
    return "\n".join(lines)


def _final_report_outline() -> str:
    return """# Final Report Outline

These notes are source material for the final English PDF report, not the final report itself.

## 1. Introduction

- Introduce CarbonRadar SME as a local, reproducible carbon data pipeline for Taiwanese SME manufacturers.
- Explain the Big Data Systems project goal: turn scattered operational CSV data into usable emissions, readiness, and demand-evidence outputs.
- Cite `README.md`, `docs/architecture.md`, and the generated Markdown or HTML report.

## 2. Target Customer

- Describe SME factories with limited ESG staff and customer disclosure pressure.
- Explain likely users: factory owner, plant manager, QA or ISO contact, ESG coordinator, finance admin, procurement staff.
- Cite `README.md` and `executive_summary.md`.

## 3. Evidence of Demand and Willingness to Pay

- Present the public-data support score, interpretation, and category sub-scores.
- Clearly state that willingness-to-pay rows are pricing hypotheses, not verified buyer behavior.
- Cite `demand_evidence_digest.md`, `data/outputs/demand_evidence_summary.md`, and `docs/demand_evidence_methodology.md`.

## 4. Product Overview

- Explain the MVP workflow: ingest sample CSVs, validate data, calculate emissions, estimate carbon-fee scenarios, score readiness, produce reports and dashboard views.
- Include screenshots from the Streamlit dashboard and HTML report.
- Cite `docs/demo_screenshot_checklist.md`.

## 5. Data Sources and Acquisition Process

- List sample factory master, utility bills, fuel logs, supplier disclosure questionnaires, emission factors, and curated public demand evidence.
- Explain that all data is local CSV data and no scraping, live APIs, OCR, database, or authentication are included.
- Cite `technical_system_summary.md`, `docs/data_dictionary.md`, and `artifact_inventory.md`.

## 6. Technical System Design

- Describe the package modules and pipeline stages from ingestion to delivery.
- Include the Mermaid architecture diagram from `docs/architecture.md`.
- Cite `technical_system_summary.md` and generated trace artifacts.

## 7. Methodology

- Scope 1/2 calculation: describe activity data multiplied by emission factors and divided by 1000.
- Carbon fee scenario: describe the simplified K-value chargeable-emissions model.
- Readiness scoring: describe weighted sub-scores and data-driven inputs.
- Demand scoring: describe confidence-weighted public-data support scoring.
- Cite `docs/methodology.md`, `docs/data_dictionary.md`, and generated CSV outputs.

## 8. Business Model

- Present pricing hypotheses: free risk scan, basic subscription, pro subscription, one-time pre-audit report, consultant/channel partner plan.
- Explain why these are hypotheses and require interviews or pilots.
- Cite `business_model_summary.md`.

## 9. Go-to-Market Difficulties

- Discuss trust, data quality, regulatory interpretation, placeholder factors, privacy, competition, and SME adoption risk.
- Pair each risk with mitigation.
- Cite `go_to_market_risks.md`.

## 10. Limitations and Future Work

- List omitted features: full Scope 3, LCA, OCR, live government refresh, database, multi-user auth, verified fuel factors, real customer data.
- Present future work in a staged roadmap.
- Cite `limitations_and_future_work.md`.

## 11. Conclusion

- Summarize the project contribution: explainable local carbon data workflow plus delivery outputs and demand-evidence support.
- Reiterate that outputs are educational/demo estimates, not legal, tax, certification, or regulatory advice.
- Cite the HTML report and artifact inventory.

## 12. Appendix

- Include screenshots, architecture diagram, command transcript, generated artifact list, factor appendix, and disclaimers.
- Cite `artifact_inventory.md`, `docs/submission_checklist.md`, and generated outputs under `data/outputs/`.
"""


def build_final_materials(org_id: str, year: int, output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    """Build report-writing source materials for the final English PDF."""

    from carbonradar.delivery.demo_bundle import run_all_demo_outputs

    artifact_paths = run_all_demo_outputs(org_id, year, output_dir=output_dir, include_final_materials=False)
    dashboard = prepare_dashboard_data(org_id, year)
    profile = dashboard.company_profile
    fee = dashboard.fee_scenario
    readiness = dashboard.readiness
    demand = dashboard.demand_score

    materials_dir = output_dir / "report_materials"

    executive_summary = f"""# Executive Summary

CarbonRadar SME is a local, reproducible carbon data workflow for Taiwanese SME manufacturers. It turns factory master data, electricity bills, fuel logs, supplier disclosure questionnaire inputs, emission factors, and curated public demand evidence into Scope 1 and Scope 2 emissions estimates, a simplified Taiwan carbon-fee scenario, a supplier disclosure readiness score, a demand public-data support score, Markdown and standalone HTML reports, and a local Streamlit dashboard.

## Target Customer

{profile["org_name"]} is the sample organization used in the demo. The broader target customer is a Taiwanese SME manufacturer with limited ESG staff that must respond to customer carbon questionnaires or prepare for carbon-fee and disclosure pressure.

## Core Value Proposition

CarbonRadar SME helps a small manufacturer organize carbon activity data, find validation issues, preserve calculation traceability, understand likely disclosure gaps, and prepare a pre-audit report before engaging consultants or certified verification bodies.

## MVP Demonstration

- Scope 1 emissions: {dashboard.annual_scope1_tco2e:.3f} tCO2e.
- Scope 2 emissions: {dashboard.annual_scope2_tco2e:.3f} tCO2e.
- Total Scope 1 + Scope 2 emissions: {dashboard.annual_total_tco2e:.3f} tCO2e.
- Readiness score: {readiness.total_score:.1f}/100 ({readiness.risk_level} risk).
- Demand score: {demand.total_demand_score:.1f}/100 ({demand.interpretation}).

This is an educational/demo project. It is not legal, tax, certification, or regulatory advice.
"""

    technical_system_summary = f"""# Technical System Summary

## Data Sources Used In v0.3.1

- Sample factory master.
- Utility bills.
- Fuel logs.
- Supplier disclosure questionnaires.
- Emission factors.
- Curated public demand evidence.

## Pipeline Stages

- Ingestion: load committed local CSV files.
- Validation and normalization: normalize months, reject missing required fields and negative values, and keep warning rows for non-fatal issues.
- Emissions calculation: calculate Scope 1 fuel and Scope 2 electricity emissions.
- Carbon-fee scenario calculation: apply a simplified K-value chargeable-emissions model.
- Readiness scoring: combine data coverage, traceability, governance, supplier response, and factor version control.
- Demand evidence scoring: score confidence-weighted public-data support.
- Report/dashboard delivery: generate CSV outputs, Markdown report, standalone HTML report, final report materials, and Streamlit dashboard views.

## Traceability Fields

- `source_document` links activity rows to synthetic bill or fuel-log documents.
- `source_dataset` identifies the source table used in each emissions trace row.
- `source_row_number` preserves row-level traceability.
- `factor_id` and `factor_year` preserve the emission factor version used in each calculation.

## Delivery Outputs

- Markdown report: `{_display_path(artifact_paths["markdown_report"])}`.
- HTML report: `{_display_path(artifact_paths["html_report"])}`.
- Demand evidence summary: `{_display_path(artifact_paths["demand_evidence_summary"])}`.

No live APIs, scraping, OCR, database, deployment infrastructure, or authentication are included.
"""

    demand_evidence_digest = f"""# Demand Evidence Digest

## Score

- Total demand score: {demand.total_demand_score:.1f}/100.
- Interpretation: {demand.interpretation}.

## Sub-Scores

{_sub_score_lines(demand.sub_scores)}

## What The Score Means

The demand score measures public-data support for the hypothesis that Taiwanese SME manufacturers need lightweight carbon data preparation, reporting, and readiness support.

## What The Score Does Not Mean

The score does not prove verified customer demand, confirmed willingness to pay, or product-market fit. Willingness-to-pay rows are pricing hypotheses, not verified buyer behavior.

## Top Supporting Evidence

{_bullet(demand.top_supporting_evidence)}

## Limitations

{_bullet(demand.key_risks)}

## Next Evidence To Collect

- Direct SME user interviews.
- Pilot users with real utility bills and fuel logs.
- Confirmed consulting and SaaS pricing benchmarks for Taiwan SME carbon workflows.
- Customer questionnaire examples from manufacturers willing to share anonymized documents.
- Updated official demand evidence before any external claim.
"""

    business_model_summary = f"""# Business Model Summary

All pricing below is a hypothesis for final project discussion, not validated pricing.

## Pricing Hypotheses

- Free risk scan: no-cost initial readiness and threshold-distance view to start conversations.
- Basic monthly subscription: lightweight CSV validation, emissions summary, and dashboard for one organization.
- Pro monthly subscription: multi-site reporting, trace exports, readiness tracking, and customer questionnaire support.
- One-time pre-audit report: fixed-fee Markdown/HTML report generation before consultant or verifier engagement.
- Consultant/channel partner plan: package CarbonRadar as a repeatable data preparation workflow for ESG consultants serving SME clients.

## Why SMEs Might Pay

- Customer questionnaires and supply-chain pressure can require faster carbon data preparation.
- SMEs may need a lower-cost pre-audit tool before paying for formal consulting or verification.
- Traceable reports can reduce manual spreadsheet work and improve internal coordination.

## Channel Partner Rationale

Consultants and channel partners may be a better early distribution path because they already have SME trust, understand local compliance context, and can review outputs before they reach customers or regulators.

## Competitive Positioning

CarbonRadar avoids competing directly with certified verifiers or enterprise ESG suites by staying focused on local data preparation, traceability, readiness scoring, and pre-audit reporting. It supports the workflow before formal assurance, not the assurance decision itself.

## Demo Scenario Reference

- Subject to direct fee: {"yes" if fee.is_subject_to_fee else "no"}.
- Chargeable emissions in demo model: {fee.chargeable_emissions_tco2e:.3f} tCO2e.
- Standard fee scenario: {_money(fee.scenario_fee_standard_ntd)}.
"""

    go_to_market_risks = """# Go-To-Market Risks

## Trust And Verification Risk

- Risk: SMEs may not trust carbon outputs without a consultant, verifier, or recognized methodology.
- Mitigation: position CarbonRadar as a pre-audit preparation tool, preserve traceability, and support consultant/channel review.

## Data Quality Risk

- Risk: input utility bills, fuel logs, and site mappings may be incomplete or inconsistent.
- Mitigation: keep validation reports, rejected-row reasons, source-document fields, and simple CSV templates.

## Legal/Regulatory Interpretation Risk

- Risk: carbon-fee applicability, K values, adjustment factors, credits, and official fee bases may change or require entity-specific review.
- Mitigation: keep disclaimers prominent and avoid presenting scenario outputs as legal or tax advice.

## Placeholder Factor Risk

- Risk: demo fuel factors are placeholders and cannot be used for real reporting.
- Mitigation: clearly mark placeholders and prioritize verified fuel factors as future work.

## Privacy/PDPA Risk

- Risk: future uploads of real bills or customer documents could contain personal or confidential business data.
- Mitigation: add data minimization, access control, retention policies, and human review before any real upload workflow.

## Competition Risk

- Risk: ESG consultants, ERP vendors, and enterprise carbon platforms may offer broader or more trusted solutions.
- Mitigation: focus on explainable SME pre-audit preparation and channel partnerships rather than certified verification.

## Customer Adoption Risk

- Risk: SMEs may lack ESG staff or time to maintain carbon data.
- Mitigation: keep workflows spreadsheet-compatible, reduce required fields, and support consultant-assisted onboarding.
"""

    limitations_and_future_work = """# Limitations And Future Work

## Current Limitations

- No full Scope 3.
- No product carbon footprint or LCA.
- No OCR.
- No live government API refresh.
- No database or multi-user authentication.
- Placeholder fuel factors.
- Demo data only.

## Future Work

- Replace placeholder fuel factors with verified sources.
- Add user CSV upload templates.
- Add a PDF renderer.
- Add OCR with human review.
- Add PostgreSQL storage.
- Add official reference data refresh.
- Add customer questionnaire export templates.
- Add deployment only if time allows.
"""

    artifact_inventory = _artifact_inventory(artifact_paths)
    final_report_outline = _final_report_outline()

    files = {
        "executive_summary": executive_summary,
        "technical_system_summary": technical_system_summary,
        "demand_evidence_digest": demand_evidence_digest,
        "business_model_summary": business_model_summary,
        "go_to_market_risks": go_to_market_risks,
        "limitations_and_future_work": limitations_and_future_work,
        "artifact_inventory": artifact_inventory,
        "final_report_outline": final_report_outline,
    }

    return {
        name: _write(materials_dir / MATERIAL_FILENAMES[name], content)
        for name, content in files.items()
    }
