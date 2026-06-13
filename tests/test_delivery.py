from carbonradar.delivery.dashboard_data import prepare_dashboard_data
from carbonradar.delivery.demo_bundle import run_all_demo_outputs


def test_dashboard_data_for_org001():
    data = prepare_dashboard_data("ORG001", 2025)

    assert data.company_profile["org_name"] == "Taiwan Precision Fasteners Co."
    assert data.annual_scope1_tco2e > 0
    assert data.annual_scope2_tco2e > 0
    assert data.annual_total_tco2e > 0
    assert not data.monthly_emissions.empty
    assert data.fee_scenario.chargeable_emissions_tco2e == 0
    assert data.readiness.total_score > 0
    assert 0 <= data.demand_score.total_demand_score <= 100


def test_run_all_demo_outputs_generates_expected_files(tmp_path):
    paths = run_all_demo_outputs("ORG001", 2025, output_dir=tmp_path)

    core_expected_keys = {
        "validation_report",
        "emissions_trace",
        "monthly_emissions",
        "annual_emissions",
        "fee_scenarios",
        "readiness",
        "markdown_report",
        "html_report",
        "demand_evidence_validation_report",
        "demand_signal_scores",
        "demand_evidence_summary",
    }
    final_material_keys = {
        "final_material_executive_summary",
        "final_material_technical_system_summary",
        "final_material_demand_evidence_digest",
        "final_material_business_model_summary",
        "final_material_go_to_market_risks",
        "final_material_limitations_and_future_work",
        "final_material_artifact_inventory",
        "final_material_final_report_outline",
    }

    assert core_expected_keys.issubset(paths)
    assert final_material_keys.issubset(paths)
    for path in paths.values():
        assert path.exists()
