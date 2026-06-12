import pandas as pd

from carbonradar.processing.validate import validate_utility_bills


def test_bill_month_normalization():
    df = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "bill_month": "2025/1",
                "kwh": 1000,
                "demand_kw": 10,
            }
        ]
    )

    valid, report = validate_utility_bills(df)

    assert report.empty
    assert valid.loc[0, "bill_month"] == "2025-01"
    assert valid.loc[0, "period_month"] == "2025-01"


def test_negative_kwh_rejection():
    df = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "bill_month": "2025-01",
                "kwh": -1,
                "demand_kw": 10,
            }
        ]
    )

    valid, report = validate_utility_bills(df)

    assert valid.empty
    assert not report.empty
    assert report.loc[0, "field"] == "kwh"
    assert "negative kWh rejected" in report.loc[0, "reason"]


def test_missing_required_fields():
    df = pd.DataFrame(
        [
            {
                "org_id": "",
                "site_id": "SITE001",
                "bill_month": "2025-01",
                "kwh": 1000,
                "demand_kw": 10,
            }
        ]
    )

    valid, report = validate_utility_bills(df)

    assert valid.empty
    assert "org_id" in set(report["field"])
    assert "missing required field" in set(report["reason"])


def test_electricity_outlier_warning_keeps_row():
    rows = [
        {
            "org_id": "ORG001",
            "site_id": "SITE001",
            "bill_month": f"2025-{month:02d}",
            "kwh": 1000,
            "demand_kw": 10,
        }
        for month in range(1, 12)
    ]
    rows.append(
        {
            "org_id": "ORG001",
            "site_id": "SITE001",
            "bill_month": "2025-12",
            "kwh": 10000,
            "demand_kw": 12,
        }
    )

    valid, report = validate_utility_bills(pd.DataFrame(rows))

    assert len(valid) == 12
    assert "warning" in set(report["severity"])
    assert "electricity outlier" in report.loc[0, "reason"]
