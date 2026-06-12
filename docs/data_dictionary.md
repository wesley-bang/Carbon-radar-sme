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

Columns: `org_id`, `site_id`, `period_month`, `activity_type`, `amount`, `unit`, `factor_id`, `factor_year`, `kgco2e_per_unit`, `emissions_tco2e`, `scope`, `source_dataset`, `source_row_number`.

