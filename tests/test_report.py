from carbonradar.ingestion.load_sample import load_sample_data
from carbonradar.processing.validate import validate_all
from carbonradar.reporting.build_markdown_report import build_markdown_report


def test_report_file_generation(tmp_path):
    data, validation_report = validate_all(load_sample_data())

    metadata = build_markdown_report(
        "ORG001",
        2025,
        data=data,
        validation_report=validation_report,
        output_dir=tmp_path,
    )

    report_path = tmp_path / "ORG001_2025_carbonradar_report.md"
    assert metadata.output_path == str(report_path)
    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")
    assert "Annual Scope 1 emissions" in content
    assert "Annual Scope 2 emissions" in content
    assert "Carbon fee scenario radar" in content
    assert "Supplier disclosure readiness score" in content
    assert "Recommended actions" in content
    assert "Legal disclaimer" in content
    assert "Demo placeholder" in content

