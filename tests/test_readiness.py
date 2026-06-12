import pandas as pd

from carbonradar.processing.readiness import score_readiness


def test_readiness_score_ranges():
    disclosure = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "year": 2025,
                "activity_data_complete": "yes",
                "bill_files_available": "yes",
                "site_mapping_complete": "yes",
                "has_esg_owner": "yes",
                "has_management_review": "yes",
                "supplier_response_rate": 100,
                "factor_version_recorded": "yes",
            },
            {
                "org_id": "ORG002",
                "year": 2025,
                "activity_data_complete": "no",
                "bill_files_available": "no",
                "site_mapping_complete": "no",
                "has_esg_owner": "no",
                "has_management_review": "no",
                "supplier_response_rate": 0,
                "factor_version_recorded": "no",
            },
        ]
    )

    high_score = score_readiness(disclosure, "ORG001", 2025)
    low_score = score_readiness(disclosure, "ORG002", 2025)

    assert high_score.total_score == 100
    assert high_score.risk_level == "Low"
    assert low_score.total_score == 0
    assert low_score.risk_level == "High"
    assert len(low_score.top_3_recommended_actions) == 3


def test_readiness_uses_validated_data_when_provided():
    disclosure = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "year": 2025,
                "activity_data_complete": "no",
                "bill_files_available": "no",
                "site_mapping_complete": "no",
                "has_esg_owner": "yes",
                "has_management_review": "yes",
                "supplier_response_rate": 80,
                "factor_version_recorded": "no",
            }
        ]
    )
    utility = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "period_month": f"2025-{month:02d}",
                "source_document": f"bill-{month:02d}",
            }
            for month in range(1, 13)
        ]
    )
    fuel = pd.DataFrame(
        [
            {
                "org_id": "ORG001",
                "site_id": "SITE001",
                "period_month": f"2025-{month:02d}",
                "source_document": "" if month == 12 else f"fuel-{month:02d}",
            }
            for month in range(1, 13)
        ]
    )
    factors = pd.DataFrame(
        [
            {
                "factor_id": "EF-ELEC",
                "factor_year": 2025,
                "source_name": "Demo source",
                "source_url": "docs/references.md",
            }
        ]
    )

    score = score_readiness(
        disclosure,
        "ORG001",
        2025,
        utility_bills=utility,
        fuel_logs=fuel,
        emission_factors=factors,
    )

    assert score.sub_scores["data_completeness"] == 30
    assert score.sub_scores["traceability"] < 25
    assert score.sub_scores["factor_version_control"] == 10
    assert score.sub_scores["governance_readiness"] == 20
    assert score.sub_scores["supplier_response_readiness"] == 12
