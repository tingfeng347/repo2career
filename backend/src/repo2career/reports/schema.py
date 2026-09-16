from __future__ import annotations

from pydantic import BaseModel, Field


class ReportContent(BaseModel):
    project_name: str
    architecture: str
    markdown: str


class ReportManifest(BaseModel):
    job_id: str
    source_kind: str
    language: str
    model: str
    parser: str | None = None
    codegraph_used: bool = False
    archify_used: bool = False
    template_id: str = "career-deep-dive"
    template_name: str = "项目深度分析与简历/面试要点"
    warnings: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
