"""Build standalone PDF-ready HTML reports."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from carbonradar.delivery.dashboard_data import monthly_emissions_pivot
from carbonradar.ingestion.load_sample import OUTPUT_DIR, load_sample_data
from carbonradar.models import ReportMetadata
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import calculate_fee_scenario
from carbonradar.processing.readiness import score_readiness
from carbonradar.processing.validate import validate_all


HTML_REPORT_SECTIONS = [
    "Company profile",
    "Boundary and assumptions",
    "Scope 1 summary",
    "Scope 2 summary",
    "Monthly emissions table",
    "Carbon fee scenario radar",
    "Supplier disclosure readiness score",
    "Missing data and recommended actions",
    "Methodology and factor version appendix",
    "Legal disclaimer",
]


def _money(value: float) -> str:
    return f"NT${value:,.0f}"


def _scope_total(annual: pd.DataFrame, scope: str) -> float:
    rows = annual[annual["scope"] == scope]
    if rows.empty:
        return 0.0
    return round(float(rows["emissions_tco2e"].sum()), 6)


def _html_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"

    header = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body_rows = []
    for _, row in df[columns].iterrows():
        cells = "".join(f"<td>{escape(str(row[column]))}</td>" for column in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def _factor_table(emission_factors: pd.DataFrame) -> pd.DataFrame:
    factor_table = emission_factors.copy()
    factor_table["placeholder_status"] = factor_table["is_demo_placeholder"].map(
        lambda value: "Demo placeholder" if str(value).strip().lower() in {"true", "yes", "1"} else "Demo factor"
    )
    return factor_table


def _company_context(factory_master: pd.DataFrame, org_id: str) -> dict[str, str]:
    rows = factory_master[factory_master["org_id"].astype(str) == org_id]
    if rows.empty:
        return {"org_name": org_id, "industry": "Unknown", "sites": ""}
    first = rows.iloc[0]
    return {
        "org_name": str(first.get("org_name", org_id)),
        "industry": str(first.get("industry", "Unknown")),
        "sites": ", ".join(rows["site_id"].astype(str).tolist()),
    }


def build_html_report(
    org_id: str,
    year: int,
    data: dict[str, pd.DataFrame] | None = None,
    validation_report: pd.DataFrame | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> ReportMetadata:
    if data is None:
        data, validation_report = validate_all(load_sample_data())
    elif validation_report is None:
        data, validation_report = validate_all(data)

    output_dir.mkdir(parents=True, exist_ok=True)

    trace, monthly, annual = calculate_emissions(data, year, org_id)
    annual_total = annual_total_tco2e(annual, org_id, year)
    fee = calculate_fee_scenario(org_id, year, annual_total)
    readiness = score_readiness(
        data["supplier_disclosure"],
        org_id,
        year,
        utility_bills=data["utility_bills"],
        fuel_logs=data["fuel_logs"],
        emission_factors=data["emission_factors"],
        validation_report=validation_report,
    )

    company = _company_context(data["factory_master"], org_id)
    scope1_total = _scope_total(annual, "Scope 1")
    scope2_total = _scope_total(annual, "Scope 2")
    monthly_table = monthly_emissions_pivot(monthly)
    factor_table = _factor_table(data["emission_factors"])

    relevant_issues = (
        validation_report[
            (validation_report["org_id"].astype(str).isin(["", org_id]))
            | (validation_report["org_id"].isna())
        ]
        if validation_report is not None and not validation_report.empty
        else pd.DataFrame()
    )
    missing_data_html = (
        "<p>No rejected rows were found for this organization in the sample data.</p>"
        if relevant_issues.empty
        else _html_table(relevant_issues, ["dataset", "row_number", "field", "severity", "reason", "original_value"])
    )
    actions_html = "".join(f"<li>{escape(action)}</li>" for action in readiness.top_3_recommended_actions)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CarbonRadar SME Report - {escape(org_id)} {year}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1f2933; line-height: 1.5; max-width: 980px; margin: 32px auto; padding: 0 24px; }}
    h1, h2 {{ color: #102a43; }}
    h1 {{ border-bottom: 3px solid #486581; padding-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 0.92rem; }}
    th, td {{ border: 1px solid #bcccdc; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f4f8; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }}
    .metric {{ border: 1px solid #bcccdc; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 1.25rem; }}
    .disclaimer {{ background: #fff7ed; border: 1px solid #fdba74; padding: 12px; }}
    @media print {{ body {{ margin: 0; max-width: none; }} }}
  </style>
</head>
<body>
  <h1>CarbonRadar SME Report: {escape(company["org_name"])} ({year})</h1>

  <h2>Company profile</h2>
  <ul>
    <li>Organization ID: {escape(org_id)}</li>
    <li>Company: {escape(company["org_name"])}</li>
    <li>Industry: {escape(company["industry"])}</li>
    <li>Sites in boundary: {escape(company["sites"])}</li>
  </ul>

  <h2>Boundary and assumptions</h2>
  <p>This demo report covers Scope 1 stationary fuel records and Scope 2 purchased electricity for calendar year {year}. It does not include OCR, live APIs, full Scope 3, product carbon footprint, ISO certification workflow, or legal interpretation.</p>

  <h2>Scope 1 summary</h2>
  <p>Annual Scope 1 emissions: <strong>{scope1_total:.3f} tCO2e</strong>.</p>

  <h2>Scope 2 summary</h2>
  <p>Annual Scope 2 emissions: <strong>{scope2_total:.3f} tCO2e</strong>.</p>
  <p>Total annual Scope 1 + Scope 2 emissions: <strong>{annual_total:.3f} tCO2e</strong>.</p>

  <h2>Monthly emissions table</h2>
  {_html_table(monthly_table, ["period_month", "scope_1_tco2e", "scope_2_tco2e", "total_tco2e"])}

  <h2>Carbon fee scenario radar</h2>
  <div class="metric-grid">
    <div class="metric">Annual emissions<strong>{fee.annual_emissions_tco2e:.3f} tCO2e</strong></div>
    <div class="metric">Remaining to threshold<strong>{fee.remaining_to_threshold_tco2e:.3f} tCO2e</strong></div>
    <div class="metric">Excess over threshold<strong>{fee.excess_over_threshold_tco2e:.3f} tCO2e</strong></div>
    <div class="metric">Subject to direct fee<strong>{"yes" if fee.is_subject_to_fee else "no"}</strong></div>
    <div class="metric">K value<strong>{fee.k_value_tco2e:.3f} tCO2e</strong></div>
    <div class="metric">Adjustment factor<strong>{fee.adjustment_factor:.3f}</strong></div>
    <div class="metric">Chargeable emissions<strong>{fee.chargeable_emissions_tco2e:.3f} tCO2e</strong></div>
    <div class="metric">Standard scenario<strong>{escape(_money(fee.scenario_fee_standard_ntd))}</strong></div>
    <div class="metric">Preferential A / B<strong>{escape(_money(fee.scenario_fee_preferential_a_ntd))} / {escape(_money(fee.scenario_fee_preferential_b_ntd))}</strong></div>
  </div>
  <p>Fee scenarios use simplified chargeable emissions after the demo K value and adjustment factor. If the organization is not subject to the fee in this demo model, scenario fees are zero.</p>

  <h2>Supplier disclosure readiness score</h2>
  <ul>
    <li>Total score: {readiness.total_score:.1f} / 100</li>
    <li>Risk level: {escape(readiness.risk_level)}</li>
    <li>Data completeness: {readiness.sub_scores["data_completeness"]:.1f} / 30</li>
    <li>Traceability: {readiness.sub_scores["traceability"]:.1f} / 25</li>
    <li>Governance readiness: {readiness.sub_scores["governance_readiness"]:.1f} / 20</li>
    <li>Supplier response readiness: {readiness.sub_scores["supplier_response_readiness"]:.1f} / 15</li>
    <li>Factor version control: {readiness.sub_scores["factor_version_control"]:.1f} / 10</li>
  </ul>

  <h2>Missing data and recommended actions</h2>
  {missing_data_html}
  <p>Recommended actions:</p>
  <ul>{actions_html}</ul>

  <h2>Methodology and factor version appendix</h2>
  <p>Scope 2 is calculated as electricity kWh x electricity kgCO2e per kWh / 1000. Scope 1 is calculated as fuel quantity x fuel kgCO2e per unit / 1000.</p>
  {_html_table(factor_table, ["factor_id", "activity_type", "unit", "factor_year", "kgco2e_per_unit", "placeholder_status", "source_name", "notes"])}
  <p>All demo placeholder fuel factors are clearly marked and must be replaced before production, regulatory, tax, or certification use.</p>

  <h2>Legal disclaimer</h2>
  <p class="disclaimer">{escape(fee.disclaimer)} Reports are for internal pre-audit planning and supplier disclosure preparation only.</p>
</body>
</html>
"""

    output_path = output_dir / f"{org_id}_{year}_carbonradar_report.html"
    output_path.write_text(html, encoding="utf-8")
    return ReportMetadata(
        org_id=org_id,
        year=year,
        output_path=str(output_path),
        generated_sections=HTML_REPORT_SECTIONS,
    )

