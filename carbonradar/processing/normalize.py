"""Normalization helpers shared by validators and calculations."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_bill_month(value: Any) -> str:
    """Normalize a month-like value to YYYY-MM, or return an empty string."""

    if value is None or pd.isna(value):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    compact = re.fullmatch(r"(\d{4})(\d{2})", text)
    if compact:
        month = int(compact.group(2))
        if not 1 <= month <= 12:
            return ""
        return f"{compact.group(1)}-{month:02d}"

    dashed = re.fullmatch(r"(\d{4})[-/](\d{1,2})", text)
    if dashed:
        month = int(dashed.group(2))
        if not 1 <= month <= 12:
            return ""
        return f"{dashed.group(1)}-{month:02d}"

    try:
        parsed = pd.to_datetime(text, errors="raise")
    except (TypeError, ValueError):
        return ""

    return f"{parsed.year:04d}-{parsed.month:02d}"


def period_year(period_month: str) -> int:
    return int(str(period_month)[:4])
