"""Build the v0.2 demand evidence Markdown report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from carbonradar.demand.load_evidence import load_demand_evidence, validate_evidence_sources
from carbonradar.demand.score_market_signals import demand_score_frame, score_market_signals
from carbonradar.ingestion.load_sample import OUTPUT_DIR, ensure_output_dir


def _table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    subset = df[columns].copy()
    if limit is not None:
        subset = subset.head(limit)
    headers = list(subset.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in subset.iterrows():
        values = [str(row[column]) for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _count_by_confidence(df: pd.DataFrame) -> str:
    if df.empty or "confidence_level" not in df.columns:
        return "none"
    counts = df["confidence_level"].value_counts().to_dict()
    return ", ".join(f"{level}: {counts[level]}" for level in sorted(counts))


def build_demand_report(
    evidence: dict[str, pd.DataFrame] | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> tuple[Path, Path]:
    evidence = evidence or load_demand_evidence()
    validation_report = validate_evidence_sources(evidence)
    score = score_market_signals(evidence)
    score_df = demand_score_frame(score)

    ensure_output_dir()
    report_path = output_dir / "demand_evidence_summary.md"
    score_path = output_dir / "demand_signal_scores.csv"
    score_df.to_csv(score_path, index=False)

    regulatory = evidence["official_regulatory_sources"]
    market = evidence["market_size_sources"]
    competitors = evidence["competitor_pricing"]
    jobs = evidence["esg_job_posting_examples"]
    procurement = evidence["public_procurement_examples"]
    wtp = evidence["willingness_to_pay_assumptions"]

    validation_text = (
        "No evidence validation issues were found."
        if validation_report.empty
        else _table(validation_report, ["dataset", "row_number", "row_id", "field", "reason"], limit=10)
    )

    content = f"""# CarbonRadar SME Demand Evidence Summary

## Target customer recap

CarbonRadar SME targets Taiwanese SME manufacturers that need a low-cost way to organize Scope 1/2 activity data, prepare supplier disclosure responses, and understand carbon-fee exposure before engaging formal consultants or verification bodies.

## Evidence collection method

v0.2 uses curated public-data evidence instead of interviews. The seed files are static CSVs committed under `data/demand_evidence/`; no scraping, live APIs, or credentialed services run at report time. Each evidence row includes source metadata, an access date, notes, and a confidence label. Rows marked `needs_verification` are treated as weak signals, not verified facts.

Validation status:

{validation_text}

## Regulatory pressure evidence

Confidence mix: {_count_by_confidence(regulatory)}

{_table(regulatory, ["source_id", "category", "key_fact", "why_it_matters", "confidence_level"], limit=8)}

## Market size evidence

Confidence mix: {_count_by_confidence(market)}

{_table(market, ["source_id", "market_segment", "metric_name", "metric_value", "unit", "year", "confidence_level"], limit=8)}

## Competitor/pricing benchmarks

Published pricing is incomplete, so quote-based rows are used as evidence that competing solutions exist, not as confirmed willingness to pay.

{_table(competitors, ["competitor_id", "competitor_name", "product_type", "pricing_model", "price_low_ntd", "price_high_ntd", "confidence_level"], limit=8)}

## Public hiring/procurement signals

Job postings and procurement examples are dynamic public signals. They indicate demand for ESG, carbon inventory, ISO 14064, sustainability reporting, or related services, but should be re-checked before external claims.

{_table(jobs, ["posting_id", "job_title", "company_or_platform", "keyword_matched", "confidence_level"], limit=8)}

{_table(procurement, ["procurement_id", "title", "buyer", "amount_ntd", "keyword_matched", "confidence_level"], limit=8)}

## Willingness-to-pay estimate

These rows are internal pricing hypotheses for the final project, not verified market facts.

{_table(wtp, ["assumption_id", "customer_segment", "pricing_hypothesis", "assumption_value", "unit", "confidence_level"], limit=8)}

## Demand signal score

- Total demand score: {score.total_demand_score:.1f} / 100
- Interpretation: {score.interpretation}
- Regulatory pressure: {score.sub_scores["regulatory_pressure_score"]:.1f} / 25
- Market size: {score.sub_scores["market_size_score"]:.1f} / 20
- Willingness to pay: {score.sub_scores["willingness_to_pay_score"]:.1f} / 20
- Competitor benchmark: {score.sub_scores["competitor_benchmark_score"]:.1f} / 15
- Hiring or procurement signal: {score.sub_scores["hiring_or_procurement_signal_score"]:.1f} / 20

This score measures public-data support for the demand hypothesis. It is not verified customer demand or confirmed willingness to pay.

Top supporting evidence:

{chr(10).join(f"- {item}" for item in score.top_supporting_evidence)}

## Limitations

{chr(10).join(f"- {risk}" for risk in score.key_risks)}

## Next evidence to collect

- Direct SME user interviews or pilots.
- Confirmed Taiwan consulting and SaaS pricing for SME carbon inventory workflows.
- Updated official SME manufacturing counts from the latest white paper.
- More official procurement cases with verified award amounts.
- Customer questionnaire examples from manufacturers willing to share anonymized documents.
"""

    report_path.write_text(content, encoding="utf-8")
    return report_path, score_path
