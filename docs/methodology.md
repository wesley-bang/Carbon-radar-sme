# Methodology

## Validation

The validator normalizes month values to `YYYY-MM`. It rejects rows with missing `org_id`, missing `site_id`, missing month, missing activity amount, invalid activity amount, negative electricity kWh, negative electricity demand, or negative fuel quantity.

Electricity outliers are flagged when a site-month kWh value is more than three standard deviations from that site's annual monthly mean. Outliers are warnings and are not silently dropped.

## Scope 2

Scope 2 emissions are calculated as:

```text
electricity kWh x electricity kgCO2e per kWh / 1000
```

The v0.1 demo electricity factor is `0.467 kgCO2e/kWh` for 2025.

## Scope 1

Scope 1 emissions are calculated as:

```text
fuel quantity x fuel kgCO2e per unit / 1000
```

Diesel and natural gas factors are demo placeholders. They must be replaced with verified sources before real use.

## Taiwan Carbon-Fee Scenarios

The v0.1 scenario parameters are:

- threshold: `25,000 tCO2e`
- standard rate: `NT$300/tCO2e`
- preferential A rate: `NT$50/tCO2e`
- preferential B rate: `NT$100/tCO2e`

Fees apply only to excess emissions above the threshold:

```text
feeable emissions = max(annual emissions - 25000, 0)
fee = feeable emissions x scenario rate
```

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

