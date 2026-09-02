from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

from repo2career.analyzers.codegraph import analyze_with_codegraph
from repo2career.analyzers.deepseek import synthesize_report
from repo2career.analyzers.scanner import scan_project
from repo2career.core.config import Settings
from repo2career.inputs.github import fetch_github_repository
from repo2career.models.domain import AnalysisJob, AnalysisStage, SourceKind
from repo2career.models.evidence import AnalysisEvidence, EvidenceRef
from repo2career.parsers.base import PdfParserKind
from repo2career.parsers.service import PdfParserService
from repo2career.reports.archify import render_archify
from repo2career.reports.render import render_report
from repo2career.reports.schema import ReportManifest

Progress = Callable[[AnalysisStage, int, str], Awaitable[None]]


class AnalysisService:
    async def run(self, job: AnalysisJob, progress: Progress) -> None:
        settings = Settings.load()
        job_dir = settings.data_dir / "jobs" / job.id
        source_dir = job_dir / "source"
        report_dir = job_dir / "report"
        await asyncio.to_thread(source_dir.mkdir, parents=True, exist_ok=True)
        await progress(AnalysisStage.INGESTING, 10, "Preparing immutable input snapshot")
        parser_name: str | None = None
        if job.source_kind == SourceKind.GITHUB:
            metadata = await fetch_github_repository(
                job.source["repository_url"], job.source.get("ref"), source_dir, settings
            )
            job.source.update(metadata)
            evidence = await self._code_evidence(
                source_dir, settings, metadata["revision"], progress
            )
        elif job.source_kind == SourceKind.FOLDER:
            evidence = await self._code_evidence(Path(job.source["path"]), settings, None, progress)
        else:
            await progress(AnalysisStage.EXTRACTING, 25, "Parsing PDF")
            requested = PdfParserKind(job.options.get("parser", "auto"))
            document = await PdfParserService(settings).parse(
                Path(job.source["path"]), requested, job.options.get("_password")
            )
            parser_name = document.parser
            evidence = self._pdf_evidence(document)
            await asyncio.to_thread(
                (job_dir / "parsed-document.json").write_text,
                document.model_dump_json(indent=2),
                encoding="utf-8",
            )
        await progress(
            AnalysisStage.ANALYZING, 60, "Synthesizing grounded project findings with DeepSeek"
        )
        content = await synthesize_report(
            evidence, settings, job.options.get("language", "zh-CN"), job.options.get("model")
        )
        await progress(AnalysisStage.DIAGRAMMING, 78, "Generating architecture artifacts")
        archify_used, archify_warning = await render_archify(content, report_dir, settings)
        if archify_warning:
            evidence.warnings.append(archify_warning)
        await progress(AnalysisStage.COMPOSING, 88, "Composing fixed report bundle")
        manifest = ReportManifest(
            job_id=job.id,
            source_kind=job.source_kind,
            language=job.options.get("language", "zh-CN"),
            model=job.options.get("model") or settings.deepseek_model,
            parser=parser_name,
            codegraph_used=bool(evidence.codegraph_summary),
            archify_used=archify_used,
            warnings=evidence.warnings,
        )
        await asyncio.to_thread(render_report, content, evidence, manifest, report_dir)
        await progress(AnalysisStage.VALIDATING, 96, "Validating report schema and evidence bundle")
        await asyncio.to_thread(self._validate_bundle, report_dir)

    async def _code_evidence(
        self, root: Path, settings: Settings, revision: str | None, progress: Progress
    ) -> AnalysisEvidence:
        await progress(AnalysisStage.INDEXING, 30, "Scanning manifests and indexing call paths")
        evidence = await asyncio.to_thread(scan_project, root, settings, revision)
        summary, warnings = await analyze_with_codegraph(root)
        evidence.codegraph_summary = summary
        evidence.warnings.extend(warnings)
        return evidence

    @staticmethod
    def _pdf_evidence(document) -> AnalysisEvidence:
        refs = [
            EvidenceRef(
                id=f"pdf-page-{page.number}",
                kind="pdf",
                path=document.filename,
                excerpt=page.text[:12000],
                page=page.number,
                category="document",
                confidence=0.95 if page.text else 0.2,
            )
            for page in document.pages
        ]
        return AnalysisEvidence(
            project_name=Path(document.filename).stem,
            source_summary=f"PDF parsed with {document.parser}; {len(document.pages)} pages",
            references=refs,
            warnings=document.warnings,
        )

    @staticmethod
    def _validate_bundle(report_dir: Path) -> None:
        required = {
            "report.md",
            "evidence.json",
            "manifest.json",
            "report-bundle.zip",
            "assets/architecture.mmd",
        }
        missing = [name for name in required if not (report_dir / name).exists()]
        if missing:
            raise RuntimeError(f"Report bundle is incomplete: {', '.join(missing)}")
        json.loads((report_dir / "manifest.json").read_text(encoding="utf-8"))
