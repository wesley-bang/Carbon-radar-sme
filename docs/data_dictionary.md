# Data Dictionary

## factory_master.csv

- `org_id`: organization identifier.
- `org_name`: synthetic company name.
- `industry`: manufacturing segment.
- `site_id`: site identifier.
- `site_name`: synthetic site name.
- `city`: Taiwan city.
- `employee_count`: sample employee count.
- `annual_revenue_band`: sample revenue band.
- `boundary_notes`: emissions boundary description.

## utility_bills.csv

- `org_id`, `site_id`: organization and site identifiers.
- `bill_month`: month, normalized to `YYYY-MM`.
- `kwh`: electricity activity amount.
- `demand_kw`: monthly demand value; negative values are rejected.
- `currency`, `cost_ntd`: sample bill cost fields.
- `source_document`: traceable synthetic bill ID.

## fuel_logs.csv

- `org_id`, `site_id`: organization and site identifiers.
- `fuel_month`: month, normalized to `YYYY-MM`.
- `fuel_type`: `diesel` or `natural_gas`.
- `quantity`: fuel activity amount; negative values are rejected.
- `unit`: `liter` for diesel and `m3` for natural gas.
- `source_document`: traceable synthetic fuel log ID.

## supplier_disclosure.csv

- `questionnaire_received`: whether a customer questionnaire exists.
- `activity_data_complete`: readiness input for data completeness.
- `bill_files_available`: readiness input for completeness and traceability.
- `site_mapping_complete`: readiness input for completeness and traceability.
- `has_esg_owner`: readiness input for governance.
- `has_management_review`: readiness input for governance.
- `supplier_response_rate`: percentage input for supplier response readiness.
- `factor_version_recorded`: readiness input for factor version control.

## emission_factors.csv

- `factor_id`: factor identifier used in calculation traces.
- `activity_type`: `electricity`, `diesel`, or `natural_gas`.
- `unit`: activity unit.
- `factor_year`: factor year.
- `kgco2e_per_unit`: factor value.
- `source_name`, `source_url`: source metadata.
- `is_demo_placeholder`: `true` for placeholder fuel factors.
- `notes`: source and limitation notes.

## Validation Report

Columns: `dataset`, `row_number`, `org_id`, `site_id`, `period_month`, `field`, `severity`, `reason`, `original_value`.

Errors reject rows. Warnings, such as electricity outliers, keep rows in the valid dataset.

## Emissions Trace

Columns: `org_id`, `site_id`, `period_month`, `activity_type`, `amount`, `unit`, `factor_id`, `factor_year`, `kgco2e_per_unit`, `emissions_tco2e`, `scope`, `source_dataset`, `source_row_number`, `source_document`.

## Fee Scenario Output

Columns: `org_id`, `year`, `annual_emissions_tco2e`, `remaining_to_threshold_tco2e`, `excess_over_threshold_tco2e`, `is_subject_to_fee`, `direct_fee_exposure_level`, `scenario_fee_standard_ntd`, `scenario_fee_preferential_a_ntd`, `scenario_fee_preferential_b_ntd`, `disclaimer`.

Scenario fees are zero when `is_subject_to_fee` is false. When true, fees are calculated against full annual emissions in this demo scenario model.

## Readiness Output

Readiness outputs include `total_score`, `risk_level`, sub-score columns, and `top_3_recommended_actions`. Data-driven scoring uses validated utility and fuel coverage plus source-document and factor metadata completeness when those dataframes are available.

## Demand Evidence Datasets

All demand evidence CSV files live in `data/demand_evidence/`. Every row includes source metadata and a confidence label.

Allowed confidence levels: `high`, `medium`, `low`, `needs_verification`.

### official_regulatory_sources.csv

Columns: `source_id`, `category`, `source_name`, `source_url`, `date_accessed`, `key_fact`, `why_it_matters`, `confidence_level`, `notes`.

### market_size_sources.csv

Columns: `source_id`, `market_segment`, `source_name`, `source_url`, `date_accessed`, `metric_name`, `metric_value`, `unit`, `year`, `why_it_matters`, `confidence_level`, `notes`.

### competitor_pricing.csv

Columns: `competitor_id`, `competitor_name`, `product_type`, `target_customer`, `pricing_model`, `price_low_ntd`, `price_high_ntd`, `currency`, `billing_period`, `source_name`, `source_url`, `date_accessed`, `notes`, `confidence_level`.

### esg_job_posting_examples.csv

Columns: `posting_id`, `job_title`, `company_or_platform`, `industry`, `location`, `keyword_matched`, `source_name`, `source_url`, `date_accessed`, `signal_type`, `notes`, `confidence_level`.

### public_procurement_examples.csv

Columns: `procurement_id`, `title`, `buyer`, `category`, `amount_ntd`, `source_name`, `source_url`, `date_accessed`, `keyword_matched`, `notes`, `confidence_level`.

### willingness_to_pay_assumptions.csv

Columns: `assumption_id`, `customer_segment`, `pricing_hypothesis`, `value_driver`, `assumption_value`, `unit`, `calculation_logic`, `confidence_level`, `notes`, `source_name`, `source_url`, `date_accessed`.

## Demand Evidence Outputs

- `demand_evidence_validation_report.csv`: validation issues for missing columns, missing source metadata, or invalid confidence levels.
- `demand_signal_scores.csv`: total demand score, interpretation, sub-scores, top supporting evidence, and key risks.
- `demand_evidence_summary.md`: Markdown summary for final project demand evidence.
