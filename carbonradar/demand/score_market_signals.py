"""Deterministic market signal scoring for v0.2 demand evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


CONFIDENCE_WEIGHTS = {
    "high": 1.0,
    "medium": 0.75,
    "low": 0.5,
    "needs_verification": 0.25,
}

SUB_SCORE_CONFIG = {
    "regulatory_pressure_score": ("official_regulatory_sources", 25.0, 5.0),
    "market_size_score": ("market_size_sources", 20.0, 4.0),
    "willingness_to_pay_score": ("willingness_to_pay_assumptions", 20.0, 5.0),
    "competitor_benchmark_score": ("competitor_pricing", 15.0, 4.0),
}

CATEGORY_PRIORITY = {
    "official_regulatory_sources": 1,
    "market_size_sources": 2,
    "competitor_pricing": 3,
    "public_procurement_examples": 4,
    "esg_job_posting_examples": 5,
    "willingness_to_pay_assumptions": 6,
}


@dataclass(frozen=True)
class DemandScoreResult:
    total_demand_score: float
    sub_scores: dict[str, float]
    top_supporting_evidence: list[str]
    key_risks: list[str]
    interpretation: str

    def to_flat_dict(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "total_demand_score": self.total_demand_score,
            "interpretation": self.interpretation,
            "top_supporting_evidence": " | ".join(self.top_supporting_evidence),
            "key_risks": " | ".join(self.key_risks),
        }
        row.update(self.sub_scores)
        return row


def _confidence_weight(value: object) -> float:
    return CONFIDENCE_WEIGHTS.get(str(value).strip().lower(), 0.0)


def _has_price(row: pd.Series) -> bool:
    return str(row.get("price_low_ntd", "")).strip() != "" or str(row.get("price_high_ntd", "")).strip() != ""


def _pricing_unavailable_explained(row: pd.Series) -> bool:
    notes = str(row.get("notes", "")).lower()
    return "unavailable" in notes or "request pricing" in notes or "quote" in notes


def _weighted_evidence_count(df: pd.DataFrame, competitor_adjustment: bool = False) -> float:
    if df.empty or "confidence_level" not in df.columns:
        return 0.0

    total = 0.0
    for _, row in df.iterrows():
        weight = _confidence_weight(row.get("confidence_level"))
        if competitor_adjustment and not _has_price(row) and not _pricing_unavailable_explained(row):
            weight *= 0.5
        total += weight
    return total


def _score_from_count(weighted_count: float, max_points: float, target_count: float) -> float:
    return round(max_points * min(weighted_count / target_count, 1.0), 2)


def _interpretation(total_score: float) -> str:
    if total_score >= 80:
        return "Strong evidence"
    if total_score >= 60:
        return "Moderate evidence"
    return "Weak / needs more validation"


def _evidence_label(dataset: str, row: pd.Series) -> str:
    name = str(row.get("source_name", row.get("pricing_hypothesis", dataset))).strip()
    if dataset == "competitor_pricing":
        subject = str(row.get("competitor_name", "")).strip()
    elif dataset == "esg_job_posting_examples":
        subject = str(row.get("job_title", "")).strip()
    elif dataset == "public_procurement_examples":
        subject = str(row.get("title", "")).strip()
    elif dataset == "willingness_to_pay_assumptions":
        subject = str(row.get("pricing_hypothesis", "")).strip()
    else:
        subject = str(row.get("key_fact", row.get("metric_name", ""))).strip()
    return f"{dataset}: {subject} ({name})"


def _top_evidence(evidence: dict[str, pd.DataFrame]) -> list[str]:
    candidates: list[tuple[int, float, str]] = []
    for dataset, df in evidence.items():
        if df.empty or "confidence_level" not in df.columns:
            continue
        for _, row in df.iterrows():
            candidates.append(
                (
                    CATEGORY_PRIORITY.get(dataset, 99),
                    -_confidence_weight(row.get("confidence_level")),
                    _evidence_label(dataset, row),
                )
            )
    candidates.sort()
    return [label for _, _, label in candidates[:5]]


def score_market_signals(evidence: dict[str, pd.DataFrame]) -> DemandScoreResult:
    sub_scores: dict[str, float] = {}

    for score_name, (dataset, max_points, target_count) in SUB_SCORE_CONFIG.items():
        df = evidence.get(dataset, pd.DataFrame())
        weighted_count = _weighted_evidence_count(df, competitor_adjustment=dataset == "competitor_pricing")
        sub_scores[score_name] = _score_from_count(weighted_count, max_points, target_count)

    jobs = evidence.get("esg_job_posting_examples", pd.DataFrame())
    procurement = evidence.get("public_procurement_examples", pd.DataFrame())
    hiring_procurement_weight = _weighted_evidence_count(jobs) + _weighted_evidence_count(procurement)
    sub_scores["hiring_or_procurement_signal_score"] = _score_from_count(hiring_procurement_weight, 20.0, 6.0)

    total = round(sum(sub_scores.values()), 2)
    return DemandScoreResult(
        total_demand_score=total,
        sub_scores=sub_scores,
        top_supporting_evidence=_top_evidence(evidence),
        key_risks=[
            "Dynamic public webpages can change after the recorded access date.",
            "Competitor pricing is often quote-based or not published.",
            "Public-data evidence supports demand hypotheses but does not replace user interviews or pilots.",
        ],
        interpretation=_interpretation(total),
    )


def demand_score_frame(result: DemandScoreResult) -> pd.DataFrame:
    return pd.DataFrame([result.to_flat_dict()])

