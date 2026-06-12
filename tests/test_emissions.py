import pandas as pd

from carbonradar.processing.emissions import calculate_scope1, calculate_scope2


def test_scope2_calculation():
    utility = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "period_month": "2025-01",
                "kwh": 10000,
                "source_row_number": 2,
                "source_document": "bill-001",
            }
        ]
    )
    factors = pd.DataFrame(
        [
            {
                "factor_id": "EF-ELEC",
                "activity_type": "electricity",
                "unit": "kWh",
                "factor_year": 2025,
                "kgco2e_per_unit": 0.467,
            }
        ]
    )

    trace = calculate_scope2(utility, factors, 2025)

    assert trace.loc[0, "scope"] == "Scope 2"
    assert trace.loc[0, "emissions_tco2e"] == 4.67
    assert trace.loc[0, "source_document"] == "bill-001"


def test_scope1_calculation():
    fuel = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "period_month": "2025-01",
                "fuel_type": "diesel",
                "quantity": 100,
                "unit": "liter",
                "source_row_number": 2,
                "source_document": "fuel-001",
            }
        ]
    )
    factors = pd.DataFrame(
        [
            {
                "factor_id": "EF-DIESEL",
                "activity_type": "diesel",
                "unit": "liter",
                "factor_year": 2025,
                "kgco2e_per_unit": 2.68,
            }
        ]
    )

    trace = calculate_scope1(fuel, factors, 2025)

    assert trace.loc[0, "scope"] == "Scope 1"
    assert trace.loc[0, "emissions_tco2e"] == 0.268
    assert trace.loc[0, "source_document"] == "fuel-001"
