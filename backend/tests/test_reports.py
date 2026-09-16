import json
import zipfile
from pathlib import Path

from repo2career.models.evidence import AnalysisEvidence, EvidenceRef
from repo2career.reports.render import render_report
from repo2career.reports.schema import ReportContent, ReportManifest


def test_report_bundle_removes_internal_evidence_markers(tmp_path: Path) -> None:
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
        architecture="Architecture",
        markdown=(
            "# Fixture 深度分析> 基于仓库/文档证据与调用关系分析生成。"
            "优先写清项目边界、业务价值、关键链路与工程取舍；没有证据的数据不要猜测。 [code-1]\n\n"
            "## 一、项目概述\n\n证据结论。[code-1]"
        ),
    )
    manifest = ReportManifest(job_id="job", source_kind="folder", language="zh-CN", model="test")
    render_report(content, evidence, manifest, tmp_path)
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    trace_report = (tmp_path / "report.trace.md").read_text(encoding="utf-8")
    assert report == (
        "# Fixture 深度分析\n\n"
        "## 一、项目概述\n\n"
        "证据结论。\n"
    )
    assert "<!-- evidence:code-1 -->" in trace_report
    assert "<!-- evidence:" not in report
    assert "[code-" not in report
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["artifacts"]
    with zipfile.ZipFile(tmp_path / "report-bundle.zip") as bundle:
        assert set(bundle.namelist()) == {
            "report.md",
            "evidence.json",
            "manifest.json",
            "assets/architecture.mmd",
        }


def test_report_manifest_records_template(tmp_path: Path) -> None:
    content = ReportContent(
        project_name="Fixture",
        architecture="Architecture",
        markdown="# Custom report",
    )
    manifest = ReportManifest(
        job_id="job",
        source_kind="pdf",
        language="en",
        model="test",
        template_id="custom-rag",
        template_name="RAG template",
    )
    render_report(
        content,
        AnalysisEvidence(project_name="Fixture", source_summary="One fixture"),
        manifest,
        tmp_path,
    )
    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert saved["template_id"] == "custom-rag"
    assert saved["template_name"] == "RAG template"
