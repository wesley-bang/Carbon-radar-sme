from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from carbonradar.delivery.dashboard_data import prepare_dashboard_data
from carbonradar.ingestion.load_sample import load_sample_data


@st.cache_data
def available_orgs_and_years() -> tuple[list[str], list[int]]:
    data = load_sample_data()
    orgs = sorted(data["factory_master"]["org_id"].astype(str).unique().tolist())
    utility_years = data["utility_bills"]["bill_month"].astype(str).str.slice(0, 4)
    fuel_years = data["fuel_logs"]["fuel_month"].astype(str).str.slice(0, 4)
    years = sorted({int(year) for year in pd.concat([utility_years, fuel_years]) if str(year).isdigit()})
    return orgs, years


@st.cache_data
def dashboard_data(org_id: str, year: int):
    return prepare_dashboard_data(org_id, year)


def money(value: float) -> str:
    return f"NT${value:,.0f}"


def main() -> None:
    st.set_page_config(page_title="CarbonRadar SME", layout="wide")
    st.title("CarbonRadar SME")
    st.caption("Local demo dashboard for Scope 1/2 emissions, carbon-fee scenarios, readiness, and demand evidence.")

    orgs, years = available_orgs_and_years()
    with st.sidebar:
        st.header("Demo controls")
        org_id = st.selectbox("Organization", orgs, index=0)
        year = st.selectbox("Year", years, index=0)
        st.markdown("---")
        st.caption("Uses committed sample CSVs only.")

    data = dashboard_data(org_id, year)
    profile = data.company_profile
    fee = data.fee_scenario
    readiness = data.readiness
    demand = data.demand_score

    st.subheader("Company profile")
    profile_cols = st.columns(4)
    profile_cols[0].metric("Company", str(profile["org_name"]))
    profile_cols[1].metric("Industry", str(profile["industry"]))
    profile_cols[2].metric("Sites", str(profile["site_count"]))
    profile_cols[3].metric("Cities", str(profile["cities"]))
    st.write(f"Boundary sites: {profile['sites']}")

    st.subheader("Annual emissions")
    metric_cols = st.columns(3)
    metric_cols[0].metric("Scope 1", f"{data.annual_scope1_tco2e:.3f} tCO2e")
    metric_cols[1].metric("Scope 2", f"{data.annual_scope2_tco2e:.3f} tCO2e")
    metric_cols[2].metric("Total", f"{data.annual_total_tco2e:.3f} tCO2e")

    st.subheader("Monthly emissions")
    st.dataframe(data.monthly_emissions, use_container_width=True)
    if not data.monthly_emissions.empty:
        chart_df = data.monthly_emissions.set_index("period_month")[
            ["scope_1_tco2e", "scope_2_tco2e", "total_tco2e"]
        ]
        st.line_chart(chart_df)

    st.subheader("Carbon fee scenario radar")
    fee_cols = st.columns(4)
    fee_cols[0].metric("Annual emissions", f"{fee.annual_emissions_tco2e:.3f} tCO2e")
    fee_cols[1].metric("Remaining to threshold", f"{fee.remaining_to_threshold_tco2e:.3f} tCO2e")
    fee_cols[2].metric("Excess over threshold", f"{fee.excess_over_threshold_tco2e:.3f} tCO2e")
    fee_cols[3].metric("Subject to fee", "yes" if fee.is_subject_to_fee else "no")

    fee_cols_2 = st.columns(4)
    fee_cols_2[0].metric("K value", f"{fee.k_value_tco2e:.0f} tCO2e")
    fee_cols_2[1].metric("Adjustment factor", f"{fee.adjustment_factor:.2f}")
    fee_cols_2[2].metric("Chargeable emissions", f"{fee.chargeable_emissions_tco2e:.3f} tCO2e")
    fee_cols_2[3].metric("Exposure level", fee.direct_fee_exposure_level)

    scenario_cols = st.columns(3)
    scenario_cols[0].metric("Standard fee", money(fee.scenario_fee_standard_ntd))
    scenario_cols[1].metric("Preferential A", money(fee.scenario_fee_preferential_a_ntd))
    scenario_cols[2].metric("Preferential B", money(fee.scenario_fee_preferential_b_ntd))

    st.subheader("Supplier disclosure readiness score")
    readiness_cols = st.columns(2)
    readiness_cols[0].metric("Total score", f"{readiness.total_score:.1f} / 100")
    readiness_cols[1].metric("Risk level", readiness.risk_level)
    st.dataframe(
        pd.DataFrame(
            [{"sub_score": key, "score": value} for key, value in readiness.sub_scores.items()]
        ),
        use_container_width=True,
    )
    st.write("Top recommended actions:")
    for action in readiness.top_3_recommended_actions:
        st.write(f"- {action}")

    st.subheader("Demand evidence score")
    demand_cols = st.columns(2)
    demand_cols[0].metric("Total demand score", f"{demand.total_demand_score:.1f} / 100")
    demand_cols[1].metric("Interpretation", demand.interpretation)
    st.dataframe(
        pd.DataFrame(
            [{"sub_score": key, "score": value} for key, value in demand.sub_scores.items()]
        ),
        use_container_width=True,
    )

    st.subheader("Disclaimers")
    st.warning(
        "Demo data only. Outputs are not legal, tax, certification, or regulatory advice. "
        "The demand score measures public-data support, not verified customer demand."
    )


if __name__ == "__main__":
    main()

