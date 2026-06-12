"""Typed records used across the v0.1 pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    dataset: str
    row_number: int
    org_id: str = ""
    site_id: str = ""
    period_month: str = ""
    field: str
    severity: str
    reason: str
    original_value: str = ""


class EmissionTraceRow(BaseModel):
    org_id: str
    site_id: str
    period_month: str
    activity_type: str
    amount: float
    unit: str
    factor_id: str
    factor_year: int
    kgco2e_per_unit: float
    emissions_tco2e: float
    scope: str
    source_dataset: str
    source_row_number: int
    source_document: str = ""


class FeeScenarioResult(BaseModel):
    org_id: str
    year: int
    annual_emissions_tco2e: float
    remaining_to_threshold_tco2e: float
    excess_over_threshold_tco2e: float
    is_subject_to_fee: bool
    k_value_tco2e: float
    adjustment_factor: float
    chargeable_emissions_tco2e: float
    direct_fee_exposure_level: str
    scenario_fee_standard_ntd: float
    scenario_fee_preferential_a_ntd: float
    scenario_fee_preferential_b_ntd: float
    disclaimer: str


class ReadinessScoreResult(BaseModel):
    org_id: str
    year: int
    total_score: float = Field(ge=0, le=100)
    sub_scores: dict[str, float]
    risk_level: str
    top_3_recommended_actions: list[str]


class ReportMetadata(BaseModel):
    org_id: str
    year: int
    output_path: str
    generated_sections: list[str]


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Return a dict for pydantic v1/v2 compatible callers."""

    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
