from __future__ import annotations

import re
import zipfile
from pathlib import Path

from repo2career.models.evidence import AnalysisEvidence
from repo2career.reports.schema import ReportContent, ReportManifest


def render_report(
    content: ReportContent, evidence: AnalysisEvidence, manifest: ReportManifest, output: Path
) -> None:
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    mermaid = _architecture_mermaid(content, evidence, manifest.language)
    (assets / "architecture.mmd").write_text(mermaid, encoding="utf-8")
    trace_report = _clean_report_markdown(content.markdown, evidence)
    public_report = _strip_evidence_metadata(trace_report)
    (output / "report.trace.md").write_text(trace_report, encoding="utf-8")
    (output / "report.md").write_text(public_report, encoding="utf-8")
    (output / "evidence.json").write_text(evidence.model_dump_json(indent=2), encoding="utf-8")
    bundle_members = ["report.md", "evidence.json", "manifest.json", "assets/architecture.mmd"]
    manifest.artifacts = [*bundle_members, "report-bundle.zip"]
    (output / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    with zipfile.ZipFile(output / "report-bundle.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for relative in bundle_members:
            bundle.write(output / relative, arcname=relative)


def _clean_report_markdown(markdown: str, evidence: AnalysisEvidence) -> str:
    """Keep provenance machine-readable without showing it in rendered Markdown."""
    report = markdown
    for reference in sorted(evidence.references, key=lambda item: len(item.id), reverse=True):
        report = re.sub(
            rf"\s*\[{re.escape(reference.id)}\]",
            f" <!-- evidence:{reference.id} -->",
            report,
        )

    report = re.sub(r">?\s*基于仓库/文档证据与调用关系分析生成。", "", report)
    report = re.sub(
        r">?\s*优先写清项目边界、业务价值、关键链路与工程取舍；没有证据的数据不要猜测。",
        "",
        report,
    )
    report = re.sub(r"(?m)^\s*>\s*$\n?", "", report)
    report = re.sub(r"\n{3,}", "\n\n", report).strip()
    return report + "\n"


def _strip_evidence_metadata(markdown: str) -> str:
    """Return the export-safe Markdown with all evidence metadata removed."""
    report = re.sub(
        r"\s*<!--\s*evidence:[A-Za-z0-9][A-Za-z0-9_.:-]*\s*-->",
        "",
        markdown,
    )
    report = re.sub(r"[ \t]+\n", "\n", report)
    report = re.sub(r"\n{3,}", "\n\n", report).strip()
    return report + "\n"


def _architecture_mermaid(content: ReportContent, evidence: AnalysisEvidence, language: str) -> str:
    english = language.lower().startswith("en")
    tech = evidence.technology[:4] or ["Application"]
    user = "User" if english else "用户"
    entry = "Project Entry" if english else "项目入口"
    data = "Data and External Services" if english else "数据与外部服务"
    lines = ["flowchart LR", f'  User["{user}"] --> App["{entry}"]']
    for index, item in enumerate(tech, start=1):
        safe = item.replace('"', "'")
        lines.append(f'  App --> T{index}["{safe}"]')
    lines.append(f'  App --> Data["{data}"]')
    return "\n".join(lines)
