from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class PdfParserKind(StrEnum):
    AUTO = "auto"
    MINERU = "mineru"
    PYPDF = "pypdf"


class ParsedPage(BaseModel):
    number: int
    text: str
    warning: str | None = None


class ParsedDocument(BaseModel):
    filename: str
    parser: PdfParserKind
    metadata: dict[str, str] = Field(default_factory=dict)
    pages: list[ParsedPage] = Field(default_factory=list)
    markdown: str = ""
    warnings: list[str] = Field(default_factory=list)
    remote_task_id: str | None = None


class PdfParser(Protocol):
    async def parse(self, path: Path, password: str | None = None) -> ParsedDocument: ...
