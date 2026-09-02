from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceKind(StrEnum):
    GITHUB = "github"
    FOLDER = "folder"
    PDF = "pdf"


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisStage(StrEnum):
    QUEUED = "queued"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    INDEXING = "indexing"
    ANALYZING = "analyzing"
    DIAGRAMMING = "diagramming"
    COMPOSING = "composing"
    VALIDATING = "validating"
    COMPLETED = "completed"


class AnalysisJob(BaseModel):
    id: str
    source_kind: SourceKind
    status: AnalysisStatus = AnalysisStatus.QUEUED
    stage: AnalysisStage = AnalysisStage.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    source: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StageEvent(BaseModel):
    id: int | None = None
    job_id: str
    stage: AnalysisStage
    progress: int
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GithubAnalysisRequest(BaseModel):
    repository_url: str
    ref: str | None = None
    language: str = "zh-CN"
    model: str | None = None


class JobAccepted(BaseModel):
    job_id: str
    status: AnalysisStatus = AnalysisStatus.QUEUED
