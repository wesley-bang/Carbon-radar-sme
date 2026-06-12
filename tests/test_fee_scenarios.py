from carbonradar.processing.fee_scenarios import calculate_fee_scenario


def test_carbon_fee_threshold_logic_chargeable_emissions():
    below = calculate_fee_scenario("ORG001", 2025, 20000)
    above = calculate_fee_scenario("ORG001", 2025, 26000)
    high = calculate_fee_scenario("ORG001", 2025, 50000)

    assert below.direct_fee_exposure_level == "Medium"
    assert below.is_subject_to_fee is False
    assert below.remaining_to_threshold_tco2e == 5000
    assert below.excess_over_threshold_tco2e == 0
    assert below.chargeable_emissions_tco2e == 0
    assert below.scenario_fee_standard_ntd == 0

    assert above.direct_fee_exposure_level == "High"
    assert above.is_subject_to_fee is True
    assert above.remaining_to_threshold_tco2e == 0
    assert above.excess_over_threshold_tco2e == 1000
    assert above.k_value_tco2e == 25000
    assert above.adjustment_factor == 1
    assert above.chargeable_emissions_tco2e == 1000
    assert above.scenario_fee_standard_ntd == 1000 * 300
    assert above.scenario_fee_preferential_a_ntd == 1000 * 50
    assert above.scenario_fee_preferential_b_ntd == 1000 * 100

    assert high.is_subject_to_fee is True
    assert high.chargeable_emissions_tco2e == 25000
    assert high.scenario_fee_standard_ntd == 25000 * 300
