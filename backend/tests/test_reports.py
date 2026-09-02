import json
import zipfile
from pathlib import Path

from repo2career.models.evidence import AnalysisEvidence, EvidenceRef
from repo2career.reports.render import render_report
from repo2career.reports.schema import ReportContent, ReportManifest


def test_report_bundle_has_fixed_sections(tmp_path: Path) -> None:
    evidence = AnalysisEvidence(
        project_name="Fixture",
        source_summary="one fixture",
        references=[
            EvidenceRef(
                id="code-1",
                kind="code",
                path="src/main.py",
                excerpt="main",
                start_line=1,
                end_line=1,
            )
        ],
    )
    content = ReportContent(
        project_name="Fixture",
        elevator_pitch="Pitch",
        business_context="Context",
        architecture="Architecture",
        star_narrative="Situation, task, action, result.",
    )
    manifest = ReportManifest(job_id="job", source_kind="folder", language="zh-CN", model="test")
    render_report(content, evidence, manifest, tmp_path)
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## 12. 面试问题与追问" in report
    assert "项目快照与分析范围" not in report
    assert "风险、证据缺口和置信度" not in report
    assert "证据索引" not in report
    assert json.loads((tmp_path / "manifest.json").read_text())["artifacts"]
    with zipfile.ZipFile(tmp_path / "report-bundle.zip") as bundle:
        assert set(bundle.namelist()) == {
            "report.md",
            "evidence.json",
            "manifest.json",
            "assets/architecture.mmd",
        }


def test_english_report_localizes_fixed_structure(tmp_path: Path) -> None:
    content = ReportContent(
        project_name="Fixture",
        elevator_pitch="Pitch",
        business_context="Context",
        architecture="Architecture",
        star_narrative="Situation, task, action, result.",
    )
    manifest = ReportManifest(job_id="job", source_kind="pdf", language="en", model="test")
    render_report(
        content,
        AnalysisEvidence(project_name="Fixture", source_summary="One fixture"),
        manifest,
        tmp_path,
    )
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## 12. Interview Questions and Follow-ups" in report
    assert "Project Snapshot and Analysis Scope" not in report
    assert "项目分析报告" not in report
