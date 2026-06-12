"""Supplier disclosure readiness scoring."""

from __future__ import annotations

import pandas as pd

from carbonradar.models import ReadinessScoreResult, model_to_dict


WEIGHTS = {
    "data_completeness": 30.0,
    "traceability": 25.0,
    "governance_readiness": 20.0,
    "supplier_response_readiness": 15.0,
    "factor_version_control": 10.0,
}

ACTION_MAP = {
    "data_completeness": "Complete missing 2025 activity data and reconcile it to bills and fuel logs.",
    "traceability": "Attach source document IDs to every site-month activity record.",
    "governance_readiness": "Assign an internal ESG owner and schedule management review.",
    "supplier_response_readiness": "Follow up with suppliers to improve questionnaire response coverage.",
    "factor_version_control": "Record emission factor year, source, URL, and placeholder status for every calculation.",
}


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _ratio(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number > 1:
        number = number / 100
    return min(max(number, 0.0), 1.0)


def risk_level(total_score: float) -> str:
    if total_score >= 80:
        return "Low"
    if total_score >= 60:
        return "Medium"
    return "High"


def _disclosure_row(supplier_disclosure: pd.DataFrame, org_id: str, year: int) -> pd.Series | None:
    rows = supplier_disclosure[
        (supplier_disclosure["org_id"].astype(str) == org_id)
        & (pd.to_numeric(supplier_disclosure["year"]) == year)
    ]
    if rows.empty:
        return None
    return rows.iloc[0]


def _governance_score(row: pd.Series | None) -> float:
    if row is None:
        return 0.0
    governance_ratio = sum(
        _truthy(row.get(field)) for field in ["has_esg_owner", "has_management_review"]
    ) / 2
    return round(governance_ratio * WEIGHTS["governance_readiness"], 2)


def _supplier_response_score(row: pd.Series | None) -> float:
    if row is None:
        return 0.0
    return round(_ratio(row.get("supplier_response_rate")) * WEIGHTS["supplier_response_readiness"], 2)


def _proxy_sub_scores(row: pd.Series | None) -> dict[str, float]:
    if row is None:
        return {name: 0.0 for name in WEIGHTS}

    completeness_ratio = sum(
        _truthy(row.get(field))
        for field in ["activity_data_complete", "bill_files_available", "site_mapping_complete"]
    ) / 3
    traceability_ratio = sum(
        _truthy(row.get(field)) for field in ["bill_files_available", "site_mapping_complete"]
    ) / 2

    return {
        "data_completeness": round(completeness_ratio * WEIGHTS["data_completeness"], 2),
        "traceability": round(traceability_ratio * WEIGHTS["traceability"], 2),
        "governance_readiness": _governance_score(row),
        "supplier_response_readiness": _supplier_response_score(row),
        "factor_version_control": round(
            (1.0 if _truthy(row.get("factor_version_recorded")) else 0.0)
            * WEIGHTS["factor_version_control"],
            2,
        ),
    }


def _year_rows(df: pd.DataFrame, org_id: str, year: int) -> pd.DataFrame:
    if df is None or df.empty or "org_id" not in df.columns or "period_month" not in df.columns:
        return pd.DataFrame()
    rows = df[df["org_id"].astype(str) == org_id].copy()
    rows = rows[rows["period_month"].astype(str).str.slice(0, 4) == str(year)]
    return rows


def _data_completeness_score(
    utility_bills: pd.DataFrame | None,
    fuel_logs: pd.DataFrame | None,
    org_id: str,
    year: int,
    validation_report: pd.DataFrame | None,
) -> float:
    utility_rows = _year_rows(utility_bills, org_id, year) if utility_bills is not None else pd.DataFrame()
    fuel_rows = _year_rows(fuel_logs, org_id, year) if fuel_logs is not None else pd.DataFrame()
    site_ids = set(utility_rows.get("site_id", pd.Series(dtype=str)).astype(str))
    site_ids.update(fuel_rows.get("site_id", pd.Series(dtype=str)).astype(str))
    site_ids.discard("")

    if not site_ids:
        return 0.0

    expected_site_months = len(site_ids) * 12
    utility_site_months = utility_rows[["site_id", "period_month"]].drop_duplicates().shape[0] if not utility_rows.empty else 0
    fuel_site_months = fuel_rows[["site_id", "period_month"]].drop_duplicates().shape[0] if not fuel_rows.empty else 0
    electricity_ratio = min(utility_site_months / expected_site_months, 1.0)
    fuel_ratio = min(fuel_site_months / expected_site_months, 1.0)
    completeness_ratio = (electricity_ratio + fuel_ratio) / 2

    if validation_report is not None and not validation_report.empty:
        org_errors = validation_report[
            (validation_report["severity"].astype(str) == "error")
            & (
                (validation_report["org_id"].astype(str) == org_id)
                | (validation_report["org_id"].isna())
                | (validation_report["org_id"].astype(str) == "")
            )
        ]
        completeness_ratio = max(completeness_ratio - min(len(org_errors) * 0.02, 0.2), 0.0)

    return round(completeness_ratio * WEIGHTS["data_completeness"], 2)


def _traceability_score(
    utility_bills: pd.DataFrame | None,
    fuel_logs: pd.DataFrame | None,
    org_id: str,
    year: int,
) -> float:
    frames = []
    for df in [utility_bills, fuel_logs]:
        rows = _year_rows(df, org_id, year) if df is not None else pd.DataFrame()
        if not rows.empty:
            frames.append(rows)

    if not frames:
        return 0.0

    combined = pd.concat(frames, ignore_index=True)
    if "source_document" not in combined.columns:
        return 0.0
    source_ratio = combined["source_document"].map(lambda value: str(value).strip() != "" and not pd.isna(value)).mean()
    return round(float(source_ratio) * WEIGHTS["traceability"], 2)


def _factor_version_score(emission_factors: pd.DataFrame | None, year: int) -> float:
    if emission_factors is None or emission_factors.empty:
        return 0.0
    rows = emission_factors[pd.to_numeric(emission_factors["factor_year"], errors="coerce") == year]
    if rows.empty:
        return 0.0
    required_columns = ["factor_id", "factor_year", "source_name", "source_url"]
    complete = rows[required_columns].apply(
        lambda column: column.map(lambda value: str(value).strip() != "" and not pd.isna(value))
    )
    return round(float(complete.all(axis=1).mean()) * WEIGHTS["factor_version_control"], 2)


def _data_driven_sub_scores(
    row: pd.Series | None,
    org_id: str,
    year: int,
    utility_bills: pd.DataFrame | None,
    fuel_logs: pd.DataFrame | None,
    emission_factors: pd.DataFrame | None,
    validation_report: pd.DataFrame | None,
) -> dict[str, float]:
    return {
        "data_completeness": _data_completeness_score(utility_bills, fuel_logs, org_id, year, validation_report),
        "traceability": _traceability_score(utility_bills, fuel_logs, org_id, year),
        "governance_readiness": _governance_score(row),
        "supplier_response_readiness": _supplier_response_score(row),
        "factor_version_control": _factor_version_score(emission_factors, year),
    }


def score_readiness(
    supplier_disclosure: pd.DataFrame,
    org_id: str,
    year: int,
    utility_bills: pd.DataFrame | None = None,
    fuel_logs: pd.DataFrame | None = None,
    emission_factors: pd.DataFrame | None = None,
    validation_report: pd.DataFrame | None = None,
) -> ReadinessScoreResult:
    row = _disclosure_row(supplier_disclosure, org_id, year)
    if any(df is not None for df in [utility_bills, fuel_logs, emission_factors, validation_report]):
        sub_scores = _data_driven_sub_scores(
            row,
            org_id,
            year,
            utility_bills,
            fuel_logs,
            emission_factors,
            validation_report,
        )
    else:
        sub_scores = _proxy_sub_scores(row)

    total = round(sum(sub_scores.values()), 2)
    gaps = sorted(
        ((WEIGHTS[name] - score, name) for name, score in sub_scores.items()),
        reverse=True,
    )
    actions = [ACTION_MAP[name] for _, name in gaps[:3]]

    return ReadinessScoreResult(
        org_id=org_id,
        year=year,
        total_score=total,
        sub_scores=sub_scores,
        risk_level=risk_level(total),
        top_3_recommended_actions=actions,
    )


def readiness_frame(result: ReadinessScoreResult) -> pd.DataFrame:
    row = model_to_dict(result)
    row.update({f"sub_score_{name}": score for name, score in result.sub_scores.items()})
    row["top_3_recommended_actions"] = " | ".join(result.top_3_recommended_actions)
    row.pop("sub_scores", None)
    return pd.DataFrame([row])
