"""Generate the full v0.3 local demo output bundle."""

from __future__ import annotations

from pathlib import Path

from carbonradar.demand.build_demand_report import build_demand_report
from carbonradar.demand.load_evidence import load_demand_evidence, validate_evidence_sources
from carbonradar.demand.score_market_signals import demand_score_frame, score_market_signals
from carbonradar.ingestion.load_sample import OUTPUT_DIR, load_sample_data
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import fee_scenario_frame
from carbonradar.processing.readiness import readiness_frame, score_readiness
from carbonradar.processing.validate import validate_all
from carbonradar.reporting.build_html_report import build_html_report
from carbonradar.reporting.build_markdown_report import build_markdown_report


def _write_csv(df, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def run_all_demo_outputs(
    org_id: str,
    year: int,
    output_dir: Path = OUTPUT_DIR,
    include_final_materials: bool = True,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    data, validation_report = validate_all(load_sample_data())
    paths["validation_report"] = _write_csv(validation_report, output_dir / "validation_report.csv")

    trace, monthly, annual = calculate_emissions(data, year, org_id)
    annual_total = annual_total_tco2e(annual, org_id, year)
    paths["emissions_trace"] = _write_csv(trace, output_dir / f"emissions_trace_{org_id}_{year}.csv")
    paths["monthly_emissions"] = _write_csv(monthly, output_dir / f"monthly_emissions_{org_id}_{year}.csv")
    paths["annual_emissions"] = _write_csv(annual, output_dir / f"annual_emissions_{org_id}_{year}.csv")
    paths["fee_scenarios"] = _write_csv(
        fee_scenario_frame(org_id, year, annual_total),
        output_dir / f"fee_scenarios_{org_id}_{year}.csv",
    )

    readiness = score_readiness(
        data["supplier_disclosure"],
        org_id,
        year,
        utility_bills=data["utility_bills"],
        fuel_logs=data["fuel_logs"],
        emission_factors=data["emission_factors"],
        validation_report=validation_report,
    )
    paths["readiness"] = _write_csv(readiness_frame(readiness), output_dir / f"readiness_{org_id}_{year}.csv")

    markdown_metadata = build_markdown_report(org_id, year, data=data, validation_report=validation_report, output_dir=output_dir)
    html_metadata = build_html_report(org_id, year, data=data, validation_report=validation_report, output_dir=output_dir)
    paths["markdown_report"] = Path(markdown_metadata.output_path)
    paths["html_report"] = Path(html_metadata.output_path)

    evidence = load_demand_evidence()
    demand_validation = validate_evidence_sources(evidence)
    demand_score = score_market_signals(evidence)
    paths["demand_evidence_validation_report"] = _write_csv(
        demand_validation,
        output_dir / "demand_evidence_validation_report.csv",
    )
    paths["demand_signal_scores"] = _write_csv(demand_score_frame(demand_score), output_dir / "demand_signal_scores.csv")
    demand_report_path, _ = build_demand_report(evidence=evidence, output_dir=output_dir)
    paths["demand_evidence_summary"] = demand_report_path

    if include_final_materials:
        from carbonradar.delivery.final_materials import build_final_materials

        material_paths = build_final_materials(org_id, year, output_dir=output_dir)
        paths.update({f"final_material_{name}": path for name, path in material_paths.items()})

    return paths
