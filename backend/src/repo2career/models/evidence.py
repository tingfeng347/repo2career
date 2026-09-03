from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    id: str
    kind: Literal["code", "pdf", "markdown", "metadata"]
    path: str
    excerpt: str
    start_line: int | None = None
    end_line: int | None = None
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    revision: str | None = None
    category: str = "general"
    confidence: float = Field(default=1.0, ge=0, le=1)


class ProjectInsight(BaseModel):
    category: str
    title: str
    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


class AnalysisEvidence(BaseModel):
    project_name: str
    source_summary: str
    technology: list[str] = Field(default_factory=list)
    tree: list[str] = Field(default_factory=list)
    references: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    codegraph_summary: str = ""
