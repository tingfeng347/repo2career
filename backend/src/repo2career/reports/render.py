from __future__ import annotations

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
    report = _markdown(content, evidence, manifest, mermaid)
    (output / "report.md").write_text(report, encoding="utf-8")
    (output / "evidence.json").write_text(evidence.model_dump_json(indent=2), encoding="utf-8")
    bundle_members = ["report.md", "evidence.json", "manifest.json", "assets/architecture.mmd"]
    manifest.artifacts = [*bundle_members, "report-bundle.zip"]
    (output / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    with zipfile.ZipFile(output / "report-bundle.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for relative in bundle_members:
            bundle.write(output / relative, arcname=relative)


def _bullets(values: list[str], empty: str = "证据不足，未生成。") -> str:
    return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"


def _markdown(
    content: ReportContent, evidence: AnalysisEvidence, manifest: ReportManifest, mermaid: str
) -> str:
    english = manifest.language.lower().startswith("en")
    headings = (
        [
            "One-minute Project Introduction",
            "Business Context, Actors, and Core Value",
            "Complete End-to-end Business Flow",
            "Functional Modules and Use Cases",
            "Technology Choices and Rationale",
            "System Architecture",
            "Call Paths, Data Flows, APIs, and Data Models",
            "Engineering Challenges, Trade-offs, and Highlights",
            "Security, Performance, Reliability, and Maintainability",
            "Resume-ready Project Bullets",
            "STAR Project Narrative",
            "Interview Questions and Follow-ups",
        ]
        if english
        else [
            "一分钟项目介绍",
            "业务背景、用户角色与核心价值",
            "完整端到端业务流程",
            "功能模块与用例",
            "技术栈及选型依据",
            "系统架构",
            "核心调用链、数据流、接口与数据模型",
            "关键工程难点、权衡和亮点",
            "安全、性能、可靠性与可维护性",
            "简历项目描述",
            "STAR 项目讲述稿",
            "面试问题与追问",
        ]
    )
    title = (
        f"{content.project_name} Project Analysis Report"
        if english
        else f"{content.project_name} 项目分析报告"
    )
    actors = "Actors" if english else "用户角色"
    empty = "Insufficient evidence." if english else "证据不足，未生成。"
    return f"""# {title}

## 1. {headings[0]}

{content.elevator_pitch}

## 2. {headings[1]}

{content.business_context}

### {actors}
{_bullets(content.actors, empty)}

## 3. {headings[2]}
{_bullets(content.business_flows, empty)}

## 4. {headings[3]}
{_bullets(content.features, empty)}

## 5. {headings[4]}
{_bullets(content.technology_choices, empty)}

## 6. {headings[5]}

{content.architecture}

```mermaid
{mermaid}
```

## 7. {headings[6]}
{_bullets(content.data_and_interfaces, empty)}

## 8. {headings[7]}
{_bullets(content.engineering_challenges, empty)}

## 9. {headings[8]}
{_bullets(content.quality_attributes, empty)}

## 10. {headings[9]}
{_bullets(content.resume_bullets, empty)}

## 11. {headings[10]}

{content.star_narrative}

## 12. {headings[11]}
{_bullets(content.interview_questions, empty)}
"""


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
