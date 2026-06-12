"""Command line interface for CarbonRadar SME v0.1."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from carbonradar.ingestion.load_sample import (
    OUTPUT_DIR,
    build_sample_manifest,
    ensure_output_dir,
    load_sample_data,
)
from carbonradar.models import model_to_dict
from carbonradar.processing.emissions import annual_total_tco2e, calculate_emissions
from carbonradar.processing.fee_scenarios import fee_scenario_frame
from carbonradar.processing.readiness import readiness_frame, score_readiness
from carbonradar.processing.validate import validate_all
from carbonradar.reporting.build_markdown_report import build_markdown_report


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
    data = load_sample_data()
    result = score_readiness(data["supplier_disclosure"], args.org, args.year)
    _write_csv(readiness_frame(result), OUTPUT_DIR / f"readiness_{args.org}_{args.year}.csv")
    print(f"Readiness score for {args.org} {args.year}: {result.total_score:.1f}/100 ({result.risk_level})")
    return 0


def cmd_build_report(args: argparse.Namespace) -> int:
    data, validation_report = _validated_sample()
    metadata = build_markdown_report(args.org, args.year, data=data, validation_report=validation_report)
    print(f"Wrote report: {metadata.output_path}")
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

    readiness = score_readiness(data["supplier_disclosure"], args.org, args.year)
    _write_csv(readiness_frame(readiness), OUTPUT_DIR / f"readiness_{args.org}_{args.year}.csv")

    metadata = build_markdown_report(args.org, args.year, data=data, validation_report=validation_report)
    print(f"Demo complete for {args.org} {args.year}")
    print(f"Annual emissions: {total:.3f} tCO2e")
    print(f"Readiness: {readiness.total_score:.1f}/100 ({readiness.risk_level})")
    print(f"Report: {metadata.output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="carbonradar", description="CarbonRadar SME v0.1 local pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "ingest-sample": (cmd_ingest_sample, False),
        "validate": (cmd_validate, False),
        "calc-emissions": (cmd_calc_emissions, True),
        "score-readiness": (cmd_score_readiness, True),
        "build-report": (cmd_build_report, True),
        "run-demo": (cmd_run_demo, True),
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

