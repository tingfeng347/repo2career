from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from repo2career.api.dependencies import job_repository
from repo2career.core.config import Settings
from repo2career.db.jobs import JobRepository
from repo2career.inputs.workspace import safe_relative_path, should_include
from repo2career.models.domain import SourceKind

router = APIRouter(prefix="/analyses", tags=["artifacts"])


async def _pdf_source_path(job_id: str, repository: JobRepository) -> tuple[Path, str]:
    job = await repository.get(job_id)
    if not job:
        raise HTTPException(404, "Analysis job not found")
    if job.source_kind != SourceKind.PDF:
        raise HTTPException(404, "PDF source not found")
    source_path = job.source.get("path")
    source = Path(source_path) if isinstance(source_path, str) else None
    if not source or source.suffix.lower() != ".pdf" or not source.is_file():
        raise HTTPException(404, "PDF source not found")
    return source, str(job.source.get("name") or source.name)


@router.get("/{job_id}/source.pdf")
async def pdf_source(
    job_id: str, repository: Annotated[JobRepository, Depends(job_repository)]
) -> FileResponse:
    source, name = await _pdf_source_path(job_id, repository)
    return FileResponse(
        source,
        media_type="application/pdf",
        filename=name,
        content_disposition_type="inline",
    )


@router.get("/{job_id}/source/content")
async def pdf_source_content(
    job_id: str, repository: Annotated[JobRepository, Depends(job_repository)]
) -> FileResponse:
    source, _ = await _pdf_source_path(job_id, repository)
    return FileResponse(source, media_type="application/octet-stream")


async def _code_source_root(job_id: str, repository: JobRepository) -> Path:
    job = await repository.get(job_id)
    if not job:
        raise HTTPException(404, "Analysis job not found")
    if job.source_kind == SourceKind.GITHUB:
        root = Settings.load().data_dir / "jobs" / job_id / "source"
    elif job.source_kind == SourceKind.FOLDER:
        source_path = job.source.get("path")
        if not isinstance(source_path, str):
            raise HTTPException(404, "Code source not found")
        root = Path(source_path)
    else:
        raise HTTPException(404, "Code source not found")
    resolved = await asyncio.to_thread(root.resolve)
    if not await asyncio.to_thread(resolved.is_dir):
        raise HTTPException(404, "Code source not found")
    return resolved


@router.get("/{job_id}/source/file")
async def code_source_file(
    job_id: str,
    path: str,
    repository: Annotated[JobRepository, Depends(job_repository)],
) -> dict[str, str]:
    root = await _code_source_root(job_id, repository)
    try:
        relative = safe_relative_path(path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not should_include(relative):
        raise HTTPException(404, "Code source not found")
    target = await asyncio.to_thread((root / relative).resolve)
    if root not in target.parents or not await asyncio.to_thread(target.is_file):
        raise HTTPException(404, "Code source not found")
    maximum = Settings.load().max_source_file_size_mb * 1024 * 1024
    if (await asyncio.to_thread(target.stat)).st_size > maximum:
        raise HTTPException(413, "Source file exceeds configured size limit")
    content = await asyncio.to_thread(target.read_text, encoding="utf-8", errors="replace")
    return {"path": relative.as_posix(), "content": content}


@router.get("/{job_id}/source.md")
async def markdown_source(
    job_id: str, repository: Annotated[JobRepository, Depends(job_repository)]
) -> FileResponse:
    job = await repository.get(job_id)
    if not job:
        raise HTTPException(404, "Analysis job not found")
    if job.source_kind != SourceKind.MARKDOWN:
        raise HTTPException(404, "Markdown source not found")
    source_path = job.source.get("path")
    source = Path(source_path) if isinstance(source_path, str) else None
    valid_suffix = source and source.suffix.lower() in {".md", ".markdown", ".txt"}
    if not source or not valid_suffix or not source.is_file():
        raise HTTPException(404, "Markdown source not found")
    return FileResponse(
        source,
        media_type="text/markdown; charset=utf-8",
        filename=str(job.source.get("name") or source.name),
        content_disposition_type="inline",
    )


async def _report_root(job_id: str, repository: JobRepository) -> Path:
    if not await repository.get(job_id):
        raise HTTPException(404, "Analysis job not found")
    root = Settings.load().data_dir / "jobs" / job_id / "report"
    if not root.exists():
        raise HTTPException(404, "Report artifacts are not ready")
    return root.resolve()


@router.get("/{job_id}/artifacts")
async def artifact_manifest(
    job_id: str, repository: Annotated[JobRepository, Depends(job_repository)]
) -> FileResponse:
    root = await _report_root(job_id, repository)
    return FileResponse(root / "manifest.json", media_type="application/json")


@router.get("/{job_id}/artifacts/{artifact_path:path}")
async def artifact_file(
    job_id: str,
    artifact_path: str,
    repository: Annotated[JobRepository, Depends(job_repository)],
) -> FileResponse:
    root = await _report_root(job_id, repository)
    target = (root / artifact_path).resolve()
    if root != target and root not in target.parents:
        raise HTTPException(400, "Unsafe artifact path")
    if not target.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(target)
