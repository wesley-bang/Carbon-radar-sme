"""Validation and normalization for sample activity data."""

from __future__ import annotations

from typing import Any

import pandas as pd

from carbonradar.models import ValidationIssue, model_to_dict
from carbonradar.processing.normalize import normalize_bill_month


VALIDATION_COLUMNS = [
    "dataset",
    "row_number",
    "org_id",
    "site_id",
    "period_month",
    "field",
    "severity",
    "reason",
    "original_value",
]


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _issue(
    dataset: str,
    row_number: int,
    row: pd.Series,
    field: str,
    severity: str,
    reason: str,
    original_value: Any = "",
    period_month: str = "",
) -> ValidationIssue:
    return ValidationIssue(
        dataset=dataset,
        row_number=row_number,
        org_id="" if _is_missing(row.get("org_id")) else str(row.get("org_id")),
        site_id="" if _is_missing(row.get("site_id")) else str(row.get("site_id")),
        period_month=period_month,
        field=field,
        severity=severity,
        reason=reason,
        original_value="" if _is_missing(original_value) else str(original_value),
    )


def _report_frame(issues: list[ValidationIssue]) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)
    return pd.DataFrame([model_to_dict(issue) for issue in issues], columns=VALIDATION_COLUMNS)


def validate_utility_bills(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    issues: list[ValidationIssue] = []
    rejected_indexes: set[int] = set()

    for index, row in df.iterrows():
        row_number = int(index) + 2
        period_month = normalize_bill_month(row.get("bill_month"))

        for field in ["org_id", "site_id"]:
            if _is_missing(row.get(field)):
                issues.append(_issue("utility_bills", row_number, row, field, "error", "missing required field"))
                rejected_indexes.add(index)

        if _is_missing(row.get("bill_month")):
            issues.append(_issue("utility_bills", row_number, row, "bill_month", "error", "missing required field"))
            rejected_indexes.add(index)
        elif not period_month:
            issues.append(
                _issue(
                    "utility_bills",
                    row_number,
                    row,
                    "bill_month",
                    "error",
                    "invalid month format",
                    row.get("bill_month"),
                )
            )
            rejected_indexes.add(index)

        kwh = _to_float(row.get("kwh"))
        if kwh is None:
            issues.append(_issue("utility_bills", row_number, row, "kwh", "error", "missing or invalid activity amount"))
            rejected_indexes.add(index)
        elif kwh < 0:
            issues.append(_issue("utility_bills", row_number, row, "kwh", "error", "negative kWh rejected", kwh, period_month))
            rejected_indexes.add(index)

        demand_kw = _to_float(row.get("demand_kw"))
        if not _is_missing(row.get("demand_kw")) and demand_kw is None:
            issues.append(_issue("utility_bills", row_number, row, "demand_kw", "error", "invalid demand_kw", row.get("demand_kw"), period_month))
            rejected_indexes.add(index)
        elif demand_kw is not None and demand_kw < 0:
            issues.append(_issue("utility_bills", row_number, row, "demand_kw", "error", "negative demand_kw rejected", demand_kw, period_month))
            rejected_indexes.add(index)

    valid = df.drop(index=list(rejected_indexes)).copy()
    if not valid.empty:
        valid["period_month"] = valid["bill_month"].map(normalize_bill_month)
        valid["bill_month"] = valid["period_month"]
        valid["kwh"] = pd.to_numeric(valid["kwh"], errors="raise")
        valid["demand_kw"] = pd.to_numeric(valid["demand_kw"], errors="coerce")
        valid["source_row_number"] = valid.index + 2

        for (_, site_id), group in valid.groupby(["org_id", "site_id"]):
            std = group["kwh"].std(ddof=0)
            if pd.isna(std) or std == 0:
                continue
            mean = group["kwh"].mean()
            outliers = group[(group["kwh"] - mean).abs() > (3 * std)]
            for index, row in outliers.iterrows():
                issues.append(
                    _issue(
                        "utility_bills",
                        int(index) + 2,
                        row,
                        "kwh",
                        "warning",
                        "electricity outlier: more than 3 standard deviations from site annual monthly mean",
                        row.get("kwh"),
                        row.get("period_month"),
                    )
                )

    return valid.reset_index(drop=True), _report_frame(issues)


def validate_fuel_logs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    issues: list[ValidationIssue] = []
    rejected_indexes: set[int] = set()

    for index, row in df.iterrows():
        row_number = int(index) + 2
        period_month = normalize_bill_month(row.get("fuel_month"))

        for field in ["org_id", "site_id", "fuel_type", "unit"]:
            if _is_missing(row.get(field)):
                issues.append(_issue("fuel_logs", row_number, row, field, "error", "missing required field"))
                rejected_indexes.add(index)

        if _is_missing(row.get("fuel_month")):
            issues.append(_issue("fuel_logs", row_number, row, "fuel_month", "error", "missing required field"))
            rejected_indexes.add(index)
        elif not period_month:
            issues.append(_issue("fuel_logs", row_number, row, "fuel_month", "error", "invalid month format", row.get("fuel_month")))
            rejected_indexes.add(index)

        quantity = _to_float(row.get("quantity"))
        if quantity is None:
            issues.append(_issue("fuel_logs", row_number, row, "quantity", "error", "missing or invalid activity amount"))
            rejected_indexes.add(index)
        elif quantity < 0:
            issues.append(_issue("fuel_logs", row_number, row, "quantity", "error", "negative fuel quantity rejected", quantity, period_month))
            rejected_indexes.add(index)

    valid = df.drop(index=list(rejected_indexes)).copy()
    if not valid.empty:
        valid["period_month"] = valid["fuel_month"].map(normalize_bill_month)
        valid["fuel_month"] = valid["period_month"]
        valid["quantity"] = pd.to_numeric(valid["quantity"], errors="raise")
        valid["source_row_number"] = valid.index + 2

    return valid.reset_index(drop=True), _report_frame(issues)


def validate_all(data: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    valid_utility, utility_report = validate_utility_bills(data["utility_bills"])
    valid_fuel, fuel_report = validate_fuel_logs(data["fuel_logs"])

    validated = dict(data)
    validated["utility_bills"] = valid_utility
    validated["fuel_logs"] = valid_fuel

    report = pd.concat([utility_report, fuel_report], ignore_index=True)
    if report.empty:
        report = pd.DataFrame(columns=VALIDATION_COLUMNS)
    return validated, report

