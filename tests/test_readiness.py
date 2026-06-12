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

