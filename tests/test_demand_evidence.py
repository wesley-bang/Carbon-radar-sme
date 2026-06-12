import pandas as pd

from carbonradar.demand.build_demand_report import build_demand_report
from carbonradar.demand.load_evidence import load_demand_evidence, validate_evidence_sources
from carbonradar.demand.score_market_signals import score_market_signals


def test_demand_evidence_required_column_validation():
    evidence = load_demand_evidence()
    evidence["official_regulatory_sources"] = evidence["official_regulatory_sources"].drop(columns=["source_url"])

    report = validate_evidence_sources(evidence)

    assert not report.empty
    assert "source_url" in set(report["field"])
    assert "missing required column" in set(report["reason"])


def test_missing_source_url_produces_validation_issue():
    evidence = load_demand_evidence()
    evidence["market_size_sources"].loc[0, "source_url"] = ""

    report = validate_evidence_sources(evidence)

    assert not report.empty
    issue = report[report["field"] == "source_url"].iloc[0]
    assert issue["reason"] == "missing required source metadata"


def test_demand_score_returns_0_to_100():
    evidence = load_demand_evidence()

    score = score_market_signals(evidence)

    assert 0 <= score.total_demand_score <= 100
    assert score.interpretation in {
        "Strong public-data support",
        "Moderate public-data support",
        "Weak public-data support / needs more validation",
    }
    assert "regulatory_pressure_score" in score.sub_scores


def test_weak_demand_score_interpretation_for_empty_evidence():
    evidence = {
        "official_regulatory_sources": pd.DataFrame(columns=["confidence_level"]),
        "market_size_sources": pd.DataFrame(columns=["confidence_level"]),
        "willingness_to_pay_assumptions": pd.DataFrame(columns=["confidence_level"]),
        "competitor_pricing": pd.DataFrame(columns=["confidence_level"]),
        "esg_job_posting_examples": pd.DataFrame(columns=["confidence_level"]),
        "public_procurement_examples": pd.DataFrame(columns=["confidence_level"]),
    }

    score = score_market_signals(evidence)

    assert score.total_demand_score == 0
    assert score.interpretation == "Weak public-data support / needs more validation"


def test_demand_report_file_generation(tmp_path):
    evidence = load_demand_evidence()

    report_path, score_path = build_demand_report(evidence=evidence, output_dir=tmp_path)

    assert report_path == tmp_path / "demand_evidence_summary.md"
    assert score_path == tmp_path / "demand_signal_scores.csv"
    assert report_path.exists()
    assert score_path.exists()

    content = report_path.read_text(encoding="utf-8")
    assert "Demand signal score" in content
    assert "public-data support" in content
    assert "not verified market facts" in content
    assert "Rows marked `needs_verification` are treated as weak signals" in content
