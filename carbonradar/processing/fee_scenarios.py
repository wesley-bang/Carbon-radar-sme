"""Taiwan carbon-fee scenario simulation for v0.1."""

from __future__ import annotations

import pandas as pd

from carbonradar.models import FeeScenarioResult, model_to_dict


THRESHOLD_TCO2E = 25000.0
STANDARD_RATE_NTD_PER_TCO2E = 300.0
PREFERENTIAL_RATE_A_NTD_PER_TCO2E = 50.0
PREFERENTIAL_RATE_B_NTD_PER_TCO2E = 100.0
DISCLAIMER = (
    "Demo scenario estimate only. This is not legal, tax, certification, or regulatory advice."
)


def exposure_level(annual_emissions_tco2e: float) -> str:
    if annual_emissions_tco2e >= THRESHOLD_TCO2E:
        return "High"
    if annual_emissions_tco2e >= 15000:
        return "Medium"
    return "Low"


def calculate_fee_scenario(org_id: str, year: int, annual_emissions_tco2e: float) -> FeeScenarioResult:
    threshold_gap = annual_emissions_tco2e - THRESHOLD_TCO2E
    feeable_emissions = max(threshold_gap, 0.0)
    return FeeScenarioResult(
        org_id=org_id,
        year=year,
        annual_emissions_tco2e=round(annual_emissions_tco2e, 6),
        threshold_gap_tco2e=round(threshold_gap, 6),
        direct_fee_exposure_level=exposure_level(annual_emissions_tco2e),
        scenario_fee_standard_ntd=round(feeable_emissions * STANDARD_RATE_NTD_PER_TCO2E, 2),
        scenario_fee_preferential_a_ntd=round(feeable_emissions * PREFERENTIAL_RATE_A_NTD_PER_TCO2E, 2),
        scenario_fee_preferential_b_ntd=round(feeable_emissions * PREFERENTIAL_RATE_B_NTD_PER_TCO2E, 2),
        disclaimer=DISCLAIMER,
    )


def fee_scenario_frame(org_id: str, year: int, annual_emissions_tco2e: float) -> pd.DataFrame:
    return pd.DataFrame([model_to_dict(calculate_fee_scenario(org_id, year, annual_emissions_tco2e))])

