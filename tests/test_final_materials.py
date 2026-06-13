from pathlib import Path

from carbonradar.delivery.final_materials import MATERIAL_FILENAMES, build_final_materials


def test_build_final_materials_generates_expected_files(tmp_path):
    paths = build_final_materials("ORG001", 2025, output_dir=tmp_path)

    assert set(paths) == set(MATERIAL_FILENAMES)
    for key, filename in MATERIAL_FILENAMES.items():
        path = tmp_path / "report_materials" / filename
        assert paths[key] == path
        assert path.exists()


def test_final_report_outline_contains_assignment_sections(tmp_path):
    paths = build_final_materials("ORG001", 2025, output_dir=tmp_path)
    content = paths["final_report_outline"].read_text(encoding="utf-8")

    expected_sections = [
        "## 1. Introduction",
        "## 2. Target Customer",
        "## 3. Evidence of Demand and Willingness to Pay",
        "## 4. Product Overview",
        "## 5. Data Sources and Acquisition Process",
        "## 6. Technical System Design",
        "## 7. Methodology",
        "## 8. Business Model",
        "## 9. Go-to-Market Difficulties",
        "## 10. Limitations and Future Work",
        "## 11. Conclusion",
        "## 12. Appendix",
    ]

    for section in expected_sections:
        assert section in content


def test_artifact_inventory_includes_html_and_demand_summary(tmp_path):
    paths = build_final_materials("ORG001", 2025, output_dir=tmp_path)
    content = paths["artifact_inventory"].read_text(encoding="utf-8")

    assert "ORG001_2025_carbonradar_report.html" in content
    assert "demand_evidence_summary.md" in content


def test_readme_documents_final_report_materials():
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Final report materials" in content
    assert "build-final-materials" in content
