"""Load and validate v0.2 demand evidence seed data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMAND_EVIDENCE_DIR = PROJECT_ROOT / "data" / "demand_evidence"

CONFIDENCE_LEVELS = {"high", "medium", "low", "needs_verification"}

EVIDENCE_FILES = {
    "official_regulatory_sources": "official_regulatory_sources.csv",
    "market_size_sources": "market_size_sources.csv",
    "competitor_pricing": "competitor_pricing.csv",
    "esg_job_posting_examples": "esg_job_posting_examples.csv",
    "public_procurement_examples": "public_procurement_examples.csv",
    "willingness_to_pay_assumptions": "willingness_to_pay_assumptions.csv",
}

REQUIRED_COLUMNS = {
    "official_regulatory_sources": [
        "source_id",
        "category",
        "source_name",
        "source_url",
        "date_accessed",
        "key_fact",
        "why_it_matters",
        "confidence_level",
        "notes",
    ],
    "market_size_sources": [
        "source_id",
        "market_segment",
        "source_name",
        "source_url",
        "date_accessed",
        "metric_name",
        "metric_value",
        "unit",
        "year",
        "why_it_matters",
        "confidence_level",
        "notes",
    ],
    "competitor_pricing": [
        "competitor_id",
        "competitor_name",
        "product_type",
        "target_customer",
        "pricing_model",
        "price_low_ntd",
        "price_high_ntd",
        "currency",
        "billing_period",
        "source_name",
        "source_url",
        "date_accessed",
        "notes",
        "confidence_level",
    ],
    "esg_job_posting_examples": [
        "posting_id",
        "job_title",
        "company_or_platform",
        "industry",
        "location",
        "keyword_matched",
        "source_name",
        "source_url",
        "date_accessed",
        "signal_type",
        "notes",
        "confidence_level",
    ],
    "public_procurement_examples": [
        "procurement_id",
        "title",
        "buyer",
        "category",
        "amount_ntd",
        "source_name",
        "source_url",
        "date_accessed",
        "keyword_matched",
        "notes",
        "confidence_level",
    ],
    "willingness_to_pay_assumptions": [
        "assumption_id",
        "customer_segment",
        "pricing_hypothesis",
        "value_driver",
        "assumption_value",
        "unit",
        "calculation_logic",
        "confidence_level",
        "notes",
        "source_name",
        "source_url",
        "date_accessed",
    ],
}

ISSUE_COLUMNS = ["dataset", "row_number", "row_id", "field", "severity", "reason", "original_value"]


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _row_id(dataset: str, row: pd.Series) -> str:
    for column in ["source_id", "competitor_id", "posting_id", "procurement_id", "assumption_id"]:
        if column in row.index and not _is_missing(row.get(column)):
            return str(row.get(column))
    return dataset


def _issue(
    dataset: str,
    row_number: int,
    row_id: str,
    field: str,
    reason: str,
    original_value: Any = "",
    severity: str = "error",
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "row_number": row_number,
        "row_id": row_id,
        "field": field,
        "severity": severity,
        "reason": reason,
        "original_value": "" if _is_missing(original_value) else str(original_value),
    }


def load_demand_evidence(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    root = data_dir or DEMAND_EVIDENCE_DIR
    evidence: dict[str, pd.DataFrame] = {}
    for name, filename in EVIDENCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing demand evidence file: {path}")
        evidence[name] = pd.read_csv(path, keep_default_na=False)
    return evidence


def validate_evidence_sources(evidence: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues: list[dict[str, object]] = []

    for dataset, required_columns in REQUIRED_COLUMNS.items():
        if dataset not in evidence:
            issues.append(_issue(dataset, 0, dataset, "dataset", "missing required evidence dataset"))
            continue

        df = evidence[dataset]
        missing_columns = [column for column in required_columns if column not in df.columns]
        for column in missing_columns:
            issues.append(_issue(dataset, 0, dataset, column, "missing required column"))

        if missing_columns:
            continue

        for row_number, (_, row) in enumerate(df.iterrows(), start=2):
            row_id = _row_id(dataset, row)
            for field in ["source_name", "source_url", "date_accessed"]:
                if _is_missing(row.get(field)):
                    issues.append(_issue(dataset, row_number, row_id, field, "missing required source metadata"))

            confidence_level = str(row.get("confidence_level", "")).strip().lower()
            if confidence_level not in CONFIDENCE_LEVELS:
                issues.append(
                    _issue(
                        dataset,
                        row_number,
                        row_id,
                        "confidence_level",
                        "invalid confidence level",
                        row.get("confidence_level", ""),
                    )
                )

    if not issues:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)
