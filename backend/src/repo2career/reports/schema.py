from __future__ import annotations

from pydantic import BaseModel, Field


class ReportContent(BaseModel):
    project_name: str
    elevator_pitch: str
    business_context: str
    actors: list[str] = Field(default_factory=list)
    business_flows: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    technology_choices: list[str] = Field(default_factory=list)
    architecture: str
    data_and_interfaces: list[str] = Field(default_factory=list)
    engineering_challenges: list[str] = Field(default_factory=list)
    quality_attributes: list[str] = Field(default_factory=list)
    risks_and_gaps: list[str] = Field(default_factory=list)
    resume_bullets: list[str] = Field(default_factory=list)
    star_narrative: str
    interview_questions: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)


class ReportManifest(BaseModel):
    job_id: str
    source_kind: str
    language: str
    model: str
    parser: str | None = None
    codegraph_used: bool = False
    archify_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
