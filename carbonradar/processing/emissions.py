"""Scope 1 and Scope 2 emissions calculations."""

from __future__ import annotations

import pandas as pd

from carbonradar.models import EmissionTraceRow, model_to_dict
from carbonradar.processing.normalize import period_year


TRACE_COLUMNS = [
    "org_id",
    "site_id",
    "period_month",
    "activity_type",
    "amount",
    "unit",
    "factor_id",
    "factor_year",
    "kgco2e_per_unit",
    "emissions_tco2e",
    "scope",
    "source_dataset",
    "source_row_number",
]


def _factor_lookup(factors: pd.DataFrame, activity_type: str, year: int) -> pd.Series:
    matches = factors[
        (factors["activity_type"].astype(str).str.lower() == activity_type.lower())
        & (pd.to_numeric(factors["factor_year"]) == year)
    ]
    if matches.empty:
        raise ValueError(f"Missing emission factor for {activity_type} in {year}")
    return matches.iloc[0]


def calculate_scope2(utility_bills: pd.DataFrame, emission_factors: pd.DataFrame, year: int) -> pd.DataFrame:
    factor = _factor_lookup(emission_factors, "electricity", year)
    rows: list[dict[str, object]] = []

    for _, row in utility_bills.iterrows():
        if period_year(row["period_month"]) != year:
            continue
        amount = float(row["kwh"])
        kgco2e_per_unit = float(factor["kgco2e_per_unit"])
        rows.append(
            model_to_dict(
                EmissionTraceRow(
                    org_id=str(row["org_id"]),
                    site_id=str(row["site_id"]),
                    period_month=str(row["period_month"]),
                    activity_type="electricity",
                    amount=amount,
                    unit="kWh",
                    factor_id=str(factor["factor_id"]),
                    factor_year=int(factor["factor_year"]),
                    kgco2e_per_unit=kgco2e_per_unit,
                    emissions_tco2e=round(amount * kgco2e_per_unit / 1000, 6),
                    scope="Scope 2",
                    source_dataset="utility_bills",
                    source_row_number=int(row.get("source_row_number", 0)),
                )
            )
        )

    return pd.DataFrame(rows, columns=TRACE_COLUMNS)


def calculate_scope1(fuel_logs: pd.DataFrame, emission_factors: pd.DataFrame, year: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, row in fuel_logs.iterrows():
        if period_year(row["period_month"]) != year:
            continue
        activity_type = str(row["fuel_type"]).strip().lower()
        factor = _factor_lookup(emission_factors, activity_type, year)
        amount = float(row["quantity"])
        kgco2e_per_unit = float(factor["kgco2e_per_unit"])
        rows.append(
            model_to_dict(
                EmissionTraceRow(
                    org_id=str(row["org_id"]),
                    site_id=str(row["site_id"]),
                    period_month=str(row["period_month"]),
                    activity_type=activity_type,
                    amount=amount,
                    unit=str(row["unit"]),
                    factor_id=str(factor["factor_id"]),
                    factor_year=int(factor["factor_year"]),
                    kgco2e_per_unit=kgco2e_per_unit,
                    emissions_tco2e=round(amount * kgco2e_per_unit / 1000, 6),
                    scope="Scope 1",
                    source_dataset="fuel_logs",
                    source_row_number=int(row.get("source_row_number", 0)),
                )
            )
        )

    return pd.DataFrame(rows, columns=TRACE_COLUMNS)


def calculate_emissions(data: dict[str, pd.DataFrame], year: int, org_id: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scope2 = calculate_scope2(data["utility_bills"], data["emission_factors"], year)
    scope1 = calculate_scope1(data["fuel_logs"], data["emission_factors"], year)
    trace = pd.concat([scope1, scope2], ignore_index=True)

    if org_id:
        trace = trace[trace["org_id"] == org_id].copy()

    if trace.empty:
        monthly = pd.DataFrame(columns=["org_id", "year", "period_month", "scope", "emissions_tco2e"])
        annual = pd.DataFrame(columns=["org_id", "year", "scope", "emissions_tco2e"])
        return trace.reset_index(drop=True), monthly, annual

    trace["year"] = trace["period_month"].str.slice(0, 4).astype(int)

    monthly = (
        trace.groupby(["org_id", "year", "period_month", "scope"], as_index=False)["emissions_tco2e"]
        .sum()
        .sort_values(["org_id", "period_month", "scope"])
        .reset_index(drop=True)
    )
    monthly["emissions_tco2e"] = monthly["emissions_tco2e"].round(6)

    annual = (
        trace.groupby(["org_id", "year", "scope"], as_index=False)["emissions_tco2e"]
        .sum()
        .sort_values(["org_id", "scope"])
        .reset_index(drop=True)
    )
    annual["emissions_tco2e"] = annual["emissions_tco2e"].round(6)

    return trace.drop(columns=["year"]).reset_index(drop=True), monthly, annual


def annual_total_tco2e(annual: pd.DataFrame, org_id: str, year: int) -> float:
    rows = annual[(annual["org_id"] == org_id) & (annual["year"] == year)]
    if rows.empty:
        return 0.0
    return round(float(rows["emissions_tco2e"].sum()), 6)

