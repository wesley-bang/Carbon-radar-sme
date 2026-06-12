"""Taiwan carbon-fee scenario simulation."""

from __future__ import annotations

import pandas as pd

from carbonradar.models import FeeScenarioResult, model_to_dict


THRESHOLD_TCO2E = 25000.0
DEFAULT_K_VALUE_TCO2E = 25000.0
DEFAULT_ADJUSTMENT_FACTOR = 1.0
STANDARD_RATE_NTD_PER_TCO2E = 300.0
PREFERENTIAL_RATE_A_NTD_PER_TCO2E = 50.0
PREFERENTIAL_RATE_B_NTD_PER_TCO2E = 100.0
DISCLAIMER = (
    "This demo estimates chargeable emissions using a simplified K-value model. Actual applicability, K values, "
    "adjustment factors, leakage-risk rules, credits, and fee base depend on current regulations and entity-specific "
    "review. This is not legal, tax, certification, or regulatory advice."
)


def exposure_level(annual_emissions_tco2e: float) -> str:
    if annual_emissions_tco2e >= THRESHOLD_TCO2E:
        return "High"
    if annual_emissions_tco2e >= 15000:
        return "Medium"
    return "Low"


def calculate_fee_scenario(org_id: str, year: int, annual_emissions_tco2e: float) -> FeeScenarioResult:
    is_subject_to_fee = annual_emissions_tco2e >= THRESHOLD_TCO2E
    remaining_to_threshold = max(THRESHOLD_TCO2E - annual_emissions_tco2e, 0.0)
    excess_over_threshold = max(annual_emissions_tco2e - THRESHOLD_TCO2E, 0.0)
    chargeable_emissions = (
        max(annual_emissions_tco2e - DEFAULT_K_VALUE_TCO2E, 0.0) * DEFAULT_ADJUSTMENT_FACTOR
        if is_subject_to_fee
        else 0.0
    )
    return FeeScenarioResult(
        org_id=org_id,
        year=year,
        annual_emissions_tco2e=round(annual_emissions_tco2e, 6),
        remaining_to_threshold_tco2e=round(remaining_to_threshold, 6),
        excess_over_threshold_tco2e=round(excess_over_threshold, 6),
        is_subject_to_fee=is_subject_to_fee,
        k_value_tco2e=round(DEFAULT_K_VALUE_TCO2E, 6),
        adjustment_factor=round(DEFAULT_ADJUSTMENT_FACTOR, 6),
        chargeable_emissions_tco2e=round(chargeable_emissions, 6),
        direct_fee_exposure_level=exposure_level(annual_emissions_tco2e),
        scenario_fee_standard_ntd=round(chargeable_emissions * STANDARD_RATE_NTD_PER_TCO2E, 2),
        scenario_fee_preferential_a_ntd=round(chargeable_emissions * PREFERENTIAL_RATE_A_NTD_PER_TCO2E, 2),
        scenario_fee_preferential_b_ntd=round(chargeable_emissions * PREFERENTIAL_RATE_B_NTD_PER_TCO2E, 2),
        disclaimer=DISCLAIMER,
    )


def fee_scenario_frame(org_id: str, year: int, annual_emissions_tco2e: float) -> pd.DataFrame:
    return pd.DataFrame([model_to_dict(calculate_fee_scenario(org_id, year, annual_emissions_tco2e))])
