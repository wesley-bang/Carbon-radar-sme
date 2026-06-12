"""Build organization-year Markdown reports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from carbonradar.ingestion.load_sample import OUTPUT_DIR, ensure_output_dir, load_sample_data
from carbonradar.models import ReportMetadata
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import calculate_fee_scenario
from carbonradar.processing.readiness import score_readiness
from carbonradar.processing.validate import validate_all


REPORT_SECTIONS = [
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


def _table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No rows._"
    subset = df[columns].copy()
    headers = list(subset.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in subset.iterrows():
        values = [str(row[column]) for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _scope_total(annual: pd.DataFrame, scope: str) -> float:
    rows = annual[annual["scope"] == scope]
    if rows.empty:
        return 0.0
    return round(float(rows["emissions_tco2e"].sum()), 6)


def _monthly_pivot(monthly: pd.DataFrame) -> pd.DataFrame:
    if monthly.empty:
        return pd.DataFrame(columns=["period_month", "scope_1_tco2e", "scope_2_tco2e", "total_tco2e"])
    pivot = (
        monthly.pivot_table(
            index="period_month",
            columns="scope",
            values="emissions_tco2e",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename(columns={"Scope 1": "scope_1_tco2e", "Scope 2": "scope_2_tco2e"})
    )
    for column in ["scope_1_tco2e", "scope_2_tco2e"]:
        if column not in pivot:
            pivot[column] = 0.0
    pivot["total_tco2e"] = pivot["scope_1_tco2e"] + pivot["scope_2_tco2e"]
    return pivot[["period_month", "scope_1_tco2e", "scope_2_tco2e", "total_tco2e"]].round(6)


def build_markdown_report(
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

    ensure_output_dir()

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

    factory_rows = data["factory_master"][data["factory_master"]["org_id"].astype(str) == org_id]
    org_name = org_id if factory_rows.empty else str(factory_rows.iloc[0]["org_name"])
    industry = "Unknown" if factory_rows.empty else str(factory_rows.iloc[0]["industry"])
    sites = ", ".join(factory_rows["site_id"].astype(str).tolist())

    scope1_total = _scope_total(annual, "Scope 1")
    scope2_total = _scope_total(annual, "Scope 2")
    monthly_table = _monthly_pivot(monthly)
    factor_table = data["emission_factors"].copy()
    factor_table["placeholder_status"] = factor_table["is_demo_placeholder"].map(
        lambda value: "Demo placeholder" if str(value).strip().lower() in {"true", "yes", "1"} else "Demo factor"
    )

    relevant_issues = validation_report[
        (validation_report["org_id"].astype(str).isin(["", org_id]))
        | (validation_report["org_id"].isna())
    ] if validation_report is not None and not validation_report.empty else pd.DataFrame()

    if relevant_issues.empty:
        missing_data_text = "No rejected rows were found for this organization in the sample data."
    else:
        missing_data_text = _table(
            relevant_issues,
            ["dataset", "row_number", "field", "severity", "reason", "original_value"],
        )

    actions = "\n".join(f"- {action}" for action in readiness.top_3_recommended_actions)

    content = f"""# CarbonRadar SME Report: {org_name} ({year})

## Company profile

- Organization ID: {org_id}
- Company: {org_name}
- Industry: {industry}
- Sites in boundary: {sites}

## Boundary and assumptions

This v0.1 report covers Scope 1 stationary fuel records and Scope 2 purchased electricity for calendar year {year}. It does not include OCR, live APIs, full Scope 3, product carbon footprint, ISO certification workflow, or legal interpretation.

## Scope 1 summary

Annual Scope 1 emissions: **{scope1_total:.3f} tCO2e**.

## Scope 2 summary

Annual Scope 2 emissions: **{scope2_total:.3f} tCO2e**.

Total annual Scope 1 + Scope 2 emissions: **{annual_total:.3f} tCO2e**.

## Monthly emissions table

{_table(monthly_table, ["period_month", "scope_1_tco2e", "scope_2_tco2e", "total_tco2e"])}

## Carbon fee scenario radar

- Annual emissions: {fee.annual_emissions_tco2e:.3f} tCO2e
- Remaining to threshold: {fee.remaining_to_threshold_tco2e:.3f} tCO2e
- Excess over threshold: {fee.excess_over_threshold_tco2e:.3f} tCO2e
- Subject to direct fee: {"yes" if fee.is_subject_to_fee else "no"}
- K value: {fee.k_value_tco2e:.3f} tCO2e
- Adjustment factor: {fee.adjustment_factor:.3f}
- Chargeable emissions: {fee.chargeable_emissions_tco2e:.3f} tCO2e
- Direct fee exposure level: {fee.direct_fee_exposure_level}
- Standard scenario: {_money(fee.scenario_fee_standard_ntd)}
- Preferential A scenario: {_money(fee.scenario_fee_preferential_a_ntd)}
- Preferential B scenario: {_money(fee.scenario_fee_preferential_b_ntd)}

Fee scenarios use simplified chargeable emissions after the demo K value and adjustment factor. If the organization is not subject to the fee in this demo model, scenario fees are zero.

## Supplier disclosure readiness score

- Total score: {readiness.total_score:.1f} / 100
- Risk level: {readiness.risk_level}
- Data completeness: {readiness.sub_scores["data_completeness"]:.1f} / 30
- Traceability: {readiness.sub_scores["traceability"]:.1f} / 25
- Governance readiness: {readiness.sub_scores["governance_readiness"]:.1f} / 20
- Supplier response readiness: {readiness.sub_scores["supplier_response_readiness"]:.1f} / 15
- Factor version control: {readiness.sub_scores["factor_version_control"]:.1f} / 10

## Missing data and recommended actions

{missing_data_text}

Recommended actions:

{actions}

## Methodology and factor version appendix

Scope 2 is calculated as electricity kWh x electricity kgCO2e per kWh / 1000. Scope 1 is calculated as fuel quantity x fuel kgCO2e per unit / 1000.

{_table(factor_table, ["factor_id", "activity_type", "unit", "factor_year", "kgco2e_per_unit", "placeholder_status", "source_name", "notes"])}

All demo placeholder fuel factors are clearly marked and must be replaced before production, regulatory, tax, or certification use.

## Legal disclaimer

{fee.disclaimer} Reports are for internal pre-audit planning and supplier disclosure preparation only.
"""

    output_path = output_dir / f"{org_id}_{year}_carbonradar_report.md"
    output_path.write_text(content, encoding="utf-8")
    return ReportMetadata(
        org_id=org_id,
        year=year,
        output_path=str(output_path),
        generated_sections=REPORT_SECTIONS,
    )
