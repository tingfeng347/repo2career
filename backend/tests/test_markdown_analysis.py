import asyncio
import json
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

import repo2career.services.analysis as analysis_module
from repo2career.api.routes.analyses import analyze_markdown
from repo2career.models.domain import AnalysisJob, AnalysisStage, SourceKind
from repo2career.reports.schema import ReportContent
from repo2career.services.analysis import AnalysisService


class CapturingManager:
    def __init__(self) -> None:
        self.submission = None

    async def submit(self, source_kind, source, options, transient=None) -> AnalysisJob:
        self.submission = (source_kind, source, options, transient)
        return AnalysisJob(id="accepted", source_kind=source_kind, source=source, options=options)


@pytest.mark.asyncio
async def test_markdown_upload_creates_direct_document_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    manager = CapturingManager()
    upload = UploadFile(
        BytesIO(b"# Project\n\nDirect input"),
        filename="project.md",
        headers=Headers({"content-type": "text/markdown"}),
    )

    accepted = await analyze_markdown(upload, manager, language="zh-CN", model=None)

    assert accepted.job_id == "accepted"
    assert manager.submission is not None
    source_kind, source, options, transient = manager.submission
    assert source_kind == SourceKind.MARKDOWN
    uploaded_text = await asyncio.to_thread(
        Path(source["path"]).read_text, encoding="utf-8"
    )
    assert uploaded_text == "# Project\n\nDirect input"
    assert source["name"] == "project.md"
    assert options == {"language": "zh-CN", "model": None}
    assert transient is None


@pytest.mark.asyncio
async def test_markdown_analysis_bypasses_pdf_parsers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "incoming" / "project.md"
    source.parent.mkdir()
    source.write_text("# Project\n\nA direct Markdown project description.", encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    def fail_if_pdf_parser_is_created(*args, **kwargs):
        raise AssertionError("PDF parser must not be used for Markdown")

    async def fake_synthesize(*args, **kwargs) -> ReportContent:
        return ReportContent(
            project_name="Project",
            elevator_pitch="Pitch",
            business_context="Context",
            architecture="Architecture",
            star_narrative="STAR",
        )

    monkeypatch.setattr(analysis_module, "PdfParserService", fail_if_pdf_parser_is_created)
    monkeypatch.setattr(analysis_module, "synthesize_report", fake_synthesize)

    stages: list[AnalysisStage] = []

    async def progress(stage: AnalysisStage, percent: int, message: str) -> None:
        stages.append(stage)

    job = AnalysisJob(
        id="markdown-job",
        source_kind=SourceKind.MARKDOWN,
        source={"path": str(source), "name": "project.md"},
        options={"language": "en"},
    )
    await AnalysisService().run(job, progress)

    report_dir = tmp_path / "jobs" / job.id / "report"
    evidence = json.loads((report_dir / "evidence.json").read_text(encoding="utf-8"))
    manifest = json.loads((report_dir / "manifest.json").read_text(encoding="utf-8"))
    assert evidence["references"][0]["kind"] == "markdown"
    assert "direct Markdown" in evidence["references"][0]["excerpt"]
    assert evidence["references"][0]["start_line"] == 1
    assert evidence["references"][0]["end_line"] == 3
    assert manifest["source_kind"] == "markdown"
    assert manifest["parser"] is None
    assert AnalysisStage.EXTRACTING in stages
    assert (report_dir / "report.md").is_file()
