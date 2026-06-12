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


def score_readiness(supplier_disclosure: pd.DataFrame, org_id: str, year: int) -> ReadinessScoreResult:
    rows = supplier_disclosure[
        (supplier_disclosure["org_id"].astype(str) == org_id)
        & (pd.to_numeric(supplier_disclosure["year"]) == year)
    ]
    if rows.empty:
        sub_scores = {name: 0.0 for name in WEIGHTS}
    else:
        row = rows.iloc[0]
        completeness_ratio = sum(
            _truthy(row.get(field))
            for field in ["activity_data_complete", "bill_files_available", "site_mapping_complete"]
        ) / 3
        traceability_ratio = sum(
            _truthy(row.get(field)) for field in ["bill_files_available", "site_mapping_complete"]
        ) / 2
        governance_ratio = sum(
            _truthy(row.get(field)) for field in ["has_esg_owner", "has_management_review"]
        ) / 2

        sub_scores = {
            "data_completeness": round(completeness_ratio * WEIGHTS["data_completeness"], 2),
            "traceability": round(traceability_ratio * WEIGHTS["traceability"], 2),
            "governance_readiness": round(governance_ratio * WEIGHTS["governance_readiness"], 2),
            "supplier_response_readiness": round(
                _ratio(row.get("supplier_response_rate")) * WEIGHTS["supplier_response_readiness"], 2
            ),
            "factor_version_control": round(
                (1.0 if _truthy(row.get("factor_version_recorded")) else 0.0)
                * WEIGHTS["factor_version_control"],
                2,
            ),
        }

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

