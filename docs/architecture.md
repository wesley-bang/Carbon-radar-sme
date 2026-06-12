# Architecture

CarbonRadar SME v0.2 is a local batch pipeline. It uses committed CSV files as the data source, pandas dataframes for processing, pydantic models for typed output records, and Markdown files for reports.

## Components

- `carbonradar.ingestion`: loads deterministic sample CSVs.
- `carbonradar.processing.validate`: normalizes month fields and returns valid rows plus validation issues.
- `carbonradar.processing.emissions`: calculates Scope 1 and Scope 2 emissions and preserves calculation traces.
- `carbonradar.processing.fee_scenarios`: estimates Taiwan carbon-fee exposure using v0.1 scenario assumptions.
- `carbonradar.processing.readiness`: scores supplier disclosure readiness.
- `carbonradar.reporting`: builds organization-year Markdown reports.
- `carbonradar.demand`: loads curated public demand evidence, validates sources, scores market signals, and builds the demand evidence report.
- `carbonradar.cli`: exposes the reproducible command line workflow.

## Flow

```text
data/sample/*.csv
  -> load_sample_data()
  -> validate_all()
  -> calculate_emissions()
  -> fee_scenario_frame()
  -> score_readiness()
  -> build_markdown_report()
  -> data/outputs/*
```

```mermaid
flowchart LR
    A["data/sample CSVs"] --> B["ingestion.load_sample"]
    B --> C["processing.validate"]
    C --> D["valid activity data"]
    C --> E["validation reports"]
    D --> F["processing.emissions"]
    F --> G["emissions trace with source_document"]
    F --> H["monthly and annual summaries"]
    H --> I["processing.fee_scenarios"]
    D --> J["processing.readiness"]
    E --> J
    I --> K["reporting.build_markdown_report"]
    J --> K
    H --> K
    K --> L["data/outputs Markdown report"]
    M["validate-bad-demo in-memory bad data"] --> C
    N["data/demand_evidence CSVs"] --> O["demand.load_evidence"]
    O --> P["demand.validate_evidence_sources"]
    O --> Q["demand.score_market_signals"]
    P --> R["demand validation report"]
    Q --> S["demand signal scores"]
    O --> T["demand.build_demand_report"]
    P --> T
    Q --> T
    T --> U["demand_evidence_summary.md"]
```

No frontend, OCR, live scraping, live API connection, message queue, workflow scheduler, or deployment platform is part of v0.2.
