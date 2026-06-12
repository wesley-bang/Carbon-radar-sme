"""Command line interface for CarbonRadar SME."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from carbonradar.demand.build_demand_report import build_demand_report
from carbonradar.demand.load_evidence import load_demand_evidence, validate_evidence_sources
from carbonradar.demand.score_market_signals import demand_score_frame, score_market_signals
from carbonradar.delivery.demo_bundle import run_all_demo_outputs
from carbonradar.ingestion.load_sample import (
    OUTPUT_DIR,
    build_sample_manifest,
    ensure_output_dir,
    load_sample_data,
)
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import fee_scenario_frame
from carbonradar.processing.readiness import readiness_frame, score_readiness
from carbonradar.processing.validate import validate_all, validate_fuel_logs, validate_utility_bills
from carbonradar.reporting.build_markdown_report import build_markdown_report
from carbonradar.reporting.build_html_report import build_html_report


def _write_csv(df: pd.DataFrame, path: Path) -> Path:
    ensure_output_dir()
    df.to_csv(path, index=False)
    return path


def _validated_sample() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    data = load_sample_data()
    return validate_all(data)


def cmd_ingest_sample(_: argparse.Namespace) -> int:
    manifest = build_sample_manifest()
    path = _write_csv(manifest, OUTPUT_DIR / "sample_manifest.csv")
    print(f"Wrote sample manifest: {path}")
    print(manifest.to_string(index=False))
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    data, report = _validated_sample()
    _write_csv(report, OUTPUT_DIR / "validation_report.csv")
    _write_csv(data["utility_bills"], OUTPUT_DIR / "valid_utility_bills.csv")
    _write_csv(data["fuel_logs"], OUTPUT_DIR / "valid_fuel_logs.csv")
    error_count = int((report["severity"] == "error").sum()) if not report.empty else 0
    warning_count = int((report["severity"] == "warning").sum()) if not report.empty else 0
    print(f"Validation complete: {error_count} errors, {warning_count} warnings")
    print(f"Wrote validation outputs to {OUTPUT_DIR}")
    return 0


def _bad_demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    utility_rows = [
        {
            "org_id": "ORG_BAD",
            "site_id": "BAD-SITE-1",
            "bill_month": f"2025-{month:02d}",
            "kwh": 1000,
            "demand_kw": 50,
            "source_document": f"bad-demo-utility-{month:02d}",
        }
        for month in range(1, 12)
    ]
    utility_rows.extend(
        [
            {
                "org_id": "ORG_BAD",
                "site_id": "BAD-SITE-1",
                "bill_month": "2025-12",
                "kwh": 10000,
                "demand_kw": 55,
                "source_document": "bad-demo-utility-outlier",
            },
            {
                "org_id": "ORG_BAD",
                "site_id": "BAD-SITE-2",
                "bill_month": "2025-01",
                "kwh": -10,
                "demand_kw": 20,
                "source_document": "bad-demo-negative-kwh",
            },
            {
                "org_id": "",
                "site_id": "BAD-SITE-2",
                "bill_month": "2025-02",
                "kwh": 900,
                "demand_kw": 19,
                "source_document": "bad-demo-missing-org",
            },
            {
                "org_id": "ORG_BAD",
                "site_id": "BAD-SITE-2",
                "bill_month": "bad-month",
                "kwh": 950,
                "demand_kw": 18,
                "source_document": "bad-demo-invalid-month",
            },
        ]
    )

    fuel_rows = [
        {
            "org_id": "ORG_BAD",
            "site_id": "BAD-SITE-1",
            "fuel_month": "2025-01",
            "fuel_type": "diesel",
            "quantity": -5,
            "unit": "liter",
            "source_document": "bad-demo-negative-fuel",
        }
    ]
    return pd.DataFrame(utility_rows), pd.DataFrame(fuel_rows)


def cmd_validate_bad_demo(_: argparse.Namespace) -> int:
    utility, fuel = _bad_demo_data()
    _, utility_report = validate_utility_bills(utility)
    _, fuel_report = validate_fuel_logs(fuel)
    report = pd.concat([utility_report, fuel_report], ignore_index=True)
    path = _write_csv(report, OUTPUT_DIR / "validation_bad_demo_report.csv")
    error_count = int((report["severity"] == "error").sum()) if not report.empty else 0
    warning_count = int((report["severity"] == "warning").sum()) if not report.empty else 0
    print(f"Bad-data validation demo complete: {error_count} errors, {warning_count} warnings")
    print(f"Wrote validation demo report: {path}")
    return 0


def cmd_validate_demand_evidence(_: argparse.Namespace) -> int:
    evidence = load_demand_evidence()
    report = validate_evidence_sources(evidence)
    path = _write_csv(report, OUTPUT_DIR / "demand_evidence_validation_report.csv")
    error_count = int((report["severity"] == "error").sum()) if not report.empty else 0
    print(f"Demand evidence validation complete: {error_count} errors")
    print(f"Wrote demand evidence validation report: {path}")
    return 0


def cmd_build_demand_report(_: argparse.Namespace) -> int:
    evidence = load_demand_evidence()
    validation_report = validate_evidence_sources(evidence)
    validation_path = _write_csv(validation_report, OUTPUT_DIR / "demand_evidence_validation_report.csv")
    score = score_market_signals(evidence)
    score_path = _write_csv(demand_score_frame(score), OUTPUT_DIR / "demand_signal_scores.csv")
    report_path, _ = build_demand_report(evidence=evidence)
    print(f"Wrote demand evidence validation report: {validation_path}")
    print(f"Wrote demand signal scores: {score_path}")
    print(f"Wrote demand evidence report: {report_path}")
    print(f"Demand score: {score.total_demand_score:.1f}/100 ({score.interpretation})")
    return 0


def _emissions_for_args(args: argparse.Namespace) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data, validation_report = _validated_sample()
    trace, monthly, annual = calculate_emissions(data, args.year, args.org)
    return data, validation_report, trace, monthly, annual


def cmd_calc_emissions(args: argparse.Namespace) -> int:
    _, _, trace, monthly, annual = _emissions_for_args(args)
    _write_csv(trace, OUTPUT_DIR / f"emissions_trace_{args.org}_{args.year}.csv")
    _write_csv(monthly, OUTPUT_DIR / f"monthly_emissions_{args.org}_{args.year}.csv")
    _write_csv(annual, OUTPUT_DIR / f"annual_emissions_{args.org}_{args.year}.csv")
    total = annual_total_tco2e(annual, args.org, args.year)
    _write_csv(fee_scenario_frame(args.org, args.year, total), OUTPUT_DIR / f"fee_scenarios_{args.org}_{args.year}.csv")
    print(f"Annual Scope 1 + Scope 2 for {args.org} {args.year}: {total:.3f} tCO2e")
    return 0


def cmd_score_readiness(args: argparse.Namespace) -> int:
    data, validation_report = _validated_sample()
    result = score_readiness(
        data["supplier_disclosure"],
        args.org,
        args.year,
        utility_bills=data["utility_bills"],
        fuel_logs=data["fuel_logs"],
        emission_factors=data["emission_factors"],
        validation_report=validation_report,
    )
    _write_csv(readiness_frame(result), OUTPUT_DIR / f"readiness_{args.org}_{args.year}.csv")
    print(f"Readiness score for {args.org} {args.year}: {result.total_score:.1f}/100 ({result.risk_level})")
    return 0


def cmd_build_report(args: argparse.Namespace) -> int:
    data, validation_report = _validated_sample()
    metadata = build_markdown_report(args.org, args.year, data=data, validation_report=validation_report)
    print(f"Wrote report: {metadata.output_path}")
    return 0


def cmd_build_html_report(args: argparse.Namespace) -> int:
    data, validation_report = _validated_sample()
    metadata = build_html_report(args.org, args.year, data=data, validation_report=validation_report)
    print(f"Wrote HTML report: {metadata.output_path}")
    return 0


def cmd_run_demo(args: argparse.Namespace) -> int:
    data, validation_report = _validated_sample()
    _write_csv(validation_report, OUTPUT_DIR / "validation_report.csv")

    trace, monthly, annual = calculate_emissions(data, args.year, args.org)
    total = annual_total_tco2e(annual, args.org, args.year)
    _write_csv(trace, OUTPUT_DIR / f"emissions_trace_{args.org}_{args.year}.csv")
    _write_csv(monthly, OUTPUT_DIR / f"monthly_emissions_{args.org}_{args.year}.csv")
    _write_csv(annual, OUTPUT_DIR / f"annual_emissions_{args.org}_{args.year}.csv")
    _write_csv(fee_scenario_frame(args.org, args.year, total), OUTPUT_DIR / f"fee_scenarios_{args.org}_{args.year}.csv")

    readiness = score_readiness(
        data["supplier_disclosure"],
        args.org,
        args.year,
        utility_bills=data["utility_bills"],
        fuel_logs=data["fuel_logs"],
        emission_factors=data["emission_factors"],
        validation_report=validation_report,
    )
    _write_csv(readiness_frame(readiness), OUTPUT_DIR / f"readiness_{args.org}_{args.year}.csv")

    metadata = build_markdown_report(args.org, args.year, data=data, validation_report=validation_report)
    print(f"Demo complete for {args.org} {args.year}")
    print(f"Annual emissions: {total:.3f} tCO2e")
    print(f"Readiness: {readiness.total_score:.1f}/100 ({readiness.risk_level})")
    print(f"Report: {metadata.output_path}")
    return 0


def cmd_run_all_demo(args: argparse.Namespace) -> int:
    paths = run_all_demo_outputs(args.org, args.year)
    print(f"Full demo bundle complete for {args.org} {args.year}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="carbonradar", description="CarbonRadar SME local pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "ingest-sample": (cmd_ingest_sample, False),
        "validate": (cmd_validate, False),
        "validate-bad-demo": (cmd_validate_bad_demo, False),
        "validate-demand-evidence": (cmd_validate_demand_evidence, False),
        "build-demand-report": (cmd_build_demand_report, False),
        "calc-emissions": (cmd_calc_emissions, True),
        "score-readiness": (cmd_score_readiness, True),
        "build-report": (cmd_build_report, True),
        "build-html-report": (cmd_build_html_report, True),
        "run-demo": (cmd_run_demo, True),
        "run-all-demo": (cmd_run_all_demo, True),
    }

    for name, (handler, needs_org_year) in commands.items():
        subparser = subparsers.add_parser(name)
        if needs_org_year:
            subparser.add_argument("--org", required=True, help="Organization ID, for example ORG001")
            subparser.add_argument("--year", required=True, type=int, help="Reporting year, for example 2025")
        subparser.set_defaults(func=handler)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
