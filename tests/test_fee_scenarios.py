from carbonradar.processing.fee_scenarios import calculate_fee_scenario


def test_carbon_fee_threshold_logic_excess_only():
    below = calculate_fee_scenario("ORG001", 2025, 20000)
    above = calculate_fee_scenario("ORG001", 2025, 26000)

    assert below.direct_fee_exposure_level == "Medium"
    assert below.threshold_gap_tco2e == -5000
    assert below.scenario_fee_standard_ntd == 0

    assert above.direct_fee_exposure_level == "High"
    assert above.threshold_gap_tco2e == 1000
    assert above.scenario_fee_standard_ntd == 300000
    assert above.scenario_fee_preferential_a_ntd == 50000
    assert above.scenario_fee_preferential_b_ntd == 100000

