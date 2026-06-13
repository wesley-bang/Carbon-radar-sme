# Methodology

## Validation

The validator normalizes month values to `YYYY-MM`. It rejects rows with missing `org_id`, missing `site_id`, missing month, missing activity amount, invalid activity amount, negative electricity kWh, negative electricity demand, or negative fuel quantity.

Electricity outliers are flagged when a site-month kWh value is more than three standard deviations from that site's annual monthly mean. Outliers are warnings and are not silently dropped.

## Scope 2

Scope 2 emissions are calculated as:

```text
electricity kWh x electricity kgCO2e per kWh / 1000
```

The demo electricity factor is `0.467 kgCO2e/kWh` for 2025.

## Scope 1

Scope 1 emissions are calculated as:

```text
fuel quantity x fuel kgCO2e per unit / 1000
```

Diesel and natural gas factors are demo placeholders. They must be replaced with verified sources before real use.

## Taiwan Carbon-Fee Scenarios

The demo carbon-fee scenario parameters are:

- threshold: `25,000 tCO2e`
- standard rate: `NT$300/tCO2e`
- preferential A rate: `NT$50/tCO2e`
- preferential B rate: `NT$100/tCO2e`

The demo scenario tracks applicability separately from threshold distance:

```text
is_subject_to_fee = annual emissions >= 25000
remaining_to_threshold_tco2e = max(25000 - annual emissions, 0)
excess_over_threshold_tco2e = max(annual emissions - 25000, 0)
```

The demo scenario estimates chargeable emissions with a simplified K-value model:

```text
k_value_tco2e = 25000
adjustment_factor = 1.0
chargeable_emissions_tco2e = max(annual emissions - k_value_tco2e, 0) x adjustment_factor
```

If `is_subject_to_fee` is false, chargeable emissions and scenario fees are zero. Scenario fees are calculated from simplified chargeable emissions after the K-value step.

Exposure levels:

- High: annual emissions greater than or equal to `25,000 tCO2e`
- Medium: annual emissions greater than or equal to `15,000 tCO2e` and below `25,000 tCO2e`
- Low: below `15,000 tCO2e`

## Readiness Score

The readiness score totals 100 points:

- data completeness: 30
- traceability: 25
- governance readiness: 20
- supplier response readiness: 15
- factor version control: 10

Risk levels:

- Low: `>=80`
- Medium: `>=60`
- High: `<60`

The top three recommended actions are the largest gaps from the weighted sub-scores.

Readiness scoring can use validated activity data when provided:

- data completeness: 12 months of electricity data per site plus fuel record month coverage
- traceability: percentage of utility and fuel rows with `source_document`
- factor version control: factor rows with `factor_id`, `factor_year`, `source_name`, and `source_url`

Governance and supplier response readiness remain questionnaire-driven. If activity data is not provided, the scorer uses the original supplier disclosure proxy fields.

## Demand Evidence Public-Data Support Scoring

v0.2 adds a public-data demand evidence pipeline for the final project requirement "Evidence of Demand and Willingness to Pay." It uses curated CSV seed datasets instead of user interviews, scraping, or live APIs.

Evidence validation checks required columns, source metadata, access dates, and confidence levels. Rows are not dropped; issues are written to a validation report.

The demand score totals 100 points:

- regulatory pressure: 25
- market size: 20
- willingness to pay: 20
- competitor benchmark: 15
- hiring or procurement signal: 20

Scores use confidence-weighted evidence counts. The interpretation labels are public-data support labels, not verified demand labels. Willingness-to-pay rows are internal pricing hypotheses and must not be described as verified buyer behavior.
