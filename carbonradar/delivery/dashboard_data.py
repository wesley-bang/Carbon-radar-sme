"""Prepare reusable data for the Streamlit dashboard and delivery reports."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from carbonradar.demand.load_evidence import load_demand_evidence
from carbonradar.demand.score_market_signals import DemandScoreResult, score_market_signals
from carbonradar.ingestion.load_sample import load_sample_data
from carbonradar.models import FeeScenarioResult, ReadinessScoreResult
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import calculate_fee_scenario
from carbonradar.processing.readiness import score_readiness
from carbonradar.processing.validate import validate_all


@dataclass(frozen=True)
class DashboardData:
    org_id: str
    year: int
    company_profile: dict[str, object]
    validation_report: pd.DataFrame
    emissions_trace: pd.DataFrame
    monthly_emissions: pd.DataFrame
    annual_emissions: pd.DataFrame
    annual_scope1_tco2e: float
    annual_scope2_tco2e: float
    annual_total_tco2e: float
    fee_scenario: FeeScenarioResult
    readiness: ReadinessScoreResult
    demand_score: DemandScoreResult
    factor_table: pd.DataFrame


def _scope_total(annual: pd.DataFrame, scope: str) -> float:
    rows = annual[annual["scope"] == scope]
    if rows.empty:
        return 0.0
    return round(float(rows["emissions_tco2e"].sum()), 6)


def monthly_emissions_pivot(monthly: pd.DataFrame) -> pd.DataFrame:
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


def _company_profile(factory_master: pd.DataFrame, org_id: str) -> dict[str, object]:
    rows = factory_master[factory_master["org_id"].astype(str) == org_id]
    if rows.empty:
        return {
            "org_id": org_id,
            "org_name": org_id,
            "industry": "Unknown",
            "sites": "",
            "site_count": 0,
            "cities": "",
            "employee_count": "",
            "annual_revenue_band": "",
        }

    first = rows.iloc[0]
    return {
        "org_id": org_id,
        "org_name": str(first.get("org_name", org_id)),
        "industry": str(first.get("industry", "Unknown")),
        "sites": ", ".join(rows["site_id"].astype(str).tolist()),
        "site_count": int(rows["site_id"].nunique()),
        "cities": ", ".join(sorted(rows["city"].astype(str).unique())) if "city" in rows else "",
        "employee_count": first.get("employee_count", ""),
        "annual_revenue_band": first.get("annual_revenue_band", ""),
    }


def _factor_table(emission_factors: pd.DataFrame) -> pd.DataFrame:
    factor_table = emission_factors.copy()
    if "is_demo_placeholder" in factor_table:
        factor_table["placeholder_status"] = factor_table["is_demo_placeholder"].map(
            lambda value: "Demo placeholder" if str(value).strip().lower() in {"true", "yes", "1"} else "Demo factor"
        )
    return factor_table


def prepare_dashboard_data(org_id: str, year: int) -> DashboardData:
    data, validation_report = validate_all(load_sample_data())
    trace, monthly, annual = calculate_emissions(data, year, org_id)

    annual_scope1 = _scope_total(annual, "Scope 1")
    annual_scope2 = _scope_total(annual, "Scope 2")
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
    demand_score = score_market_signals(load_demand_evidence())

    return DashboardData(
        org_id=org_id,
        year=year,
        company_profile=_company_profile(data["factory_master"], org_id),
        validation_report=validation_report,
        emissions_trace=trace,
        monthly_emissions=monthly_emissions_pivot(monthly),
        annual_emissions=annual,
        annual_scope1_tco2e=annual_scope1,
        annual_scope2_tco2e=annual_scope2,
        annual_total_tco2e=annual_total,
        fee_scenario=fee,
        readiness=readiness,
        demand_score=demand_score,
        factor_table=_factor_table(data["emission_factors"]),
    )

