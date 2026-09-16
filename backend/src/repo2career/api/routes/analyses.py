from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Annotated

from anyio import open_file
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from repo2career.api.dependencies import job_manager
from repo2career.core.config import Settings
from repo2career.inputs.github import parse_github_url
from repo2career.models.domain import (
    GithubAnalysisRequest,
    JobAccepted,
    LocalFolderAnalysisRequest,
    SourceKind,
)
from repo2career.parsers.base import PdfParserKind
from repo2career.services.jobs import JobManager

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/github", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def analyze_github(
    request: GithubAnalysisRequest,
    manager: Annotated[JobManager, Depends(job_manager)],
) -> JobAccepted:
    try:
        parse_github_url(request.repository_url)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    job = await manager.submit(
        SourceKind.GITHUB,
        {"repository_url": request.repository_url, "ref": request.ref},
        {"language": request.language, "model": request.model, "template_id": request.template_id},
    )
    return JobAccepted(job_id=job.id)


@router.post("/local-folder", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def analyze_local_folder(
    request: LocalFolderAnalysisRequest,
    manager: Annotated[JobManager, Depends(job_manager)],
) -> JobAccepted:
    root = await asyncio.to_thread(lambda: Path(request.path).expanduser().resolve())
    if not await asyncio.to_thread(root.is_dir):
        raise HTTPException(422, "Local folder does not exist")
    job = await manager.submit(
        SourceKind.FOLDER,
        {"path": str(root), "name": root.name},
        {"language": request.language, "model": request.model, "template_id": request.template_id},
    )
    return JobAccepted(job_id=job.id)


@router.post("/pdf", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def analyze_pdf(
    file: Annotated[UploadFile, File()],
    manager: Annotated[JobManager, Depends(job_manager)],
    parser: Annotated[PdfParserKind, Form()] = PdfParserKind.AUTO,
    language: Annotated[str, Form()] = "zh-CN",
    model: Annotated[str | None, Form()] = None,
    template_id: Annotated[str, Form()] = "career-deep-dive",
    password: Annotated[str | None, Form()] = None,
) -> JobAccepted:
    settings = Settings.load()
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(415, "Only PDF files are accepted")
    target = settings.data_dir / "incoming" / f"{uuid.uuid4()}.pdf"
    await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
    total = 0
    async with await open_file(target, "wb") as output:
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_pdf_size_mb * 1024 * 1024:
                await asyncio.to_thread(target.unlink, missing_ok=True)
                raise HTTPException(413, "PDF exceeds configured size limit")
            await output.write(chunk)
    signature = await asyncio.to_thread(lambda: target.read_bytes()[:5])
    if signature != b"%PDF-":
        await asyncio.to_thread(target.unlink, missing_ok=True)
        raise HTTPException(422, "File does not have a PDF signature")
    job = await manager.submit(
        SourceKind.PDF,
        {"path": str(target), "name": file.filename or target.name, "bytes": total},
        {"language": language, "model": model, "parser": parser, "template_id": template_id},
        {"password": password} if password else None,
    )
    return JobAccepted(job_id=job.id)


@router.post("/markdown", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def analyze_markdown(
    file: Annotated[UploadFile, File()],
    manager: Annotated[JobManager, Depends(job_manager)],
    language: Annotated[str, Form()] = "zh-CN",
    model: Annotated[str | None, Form()] = None,
    template_id: Annotated[str, Form()] = "career-deep-dive",
) -> JobAccepted:
    settings = Settings.load()
    filename = file.filename or "document.md"
    if Path(filename).suffix.lower() != ".md":
        raise HTTPException(415, "Only Markdown (.md) files are accepted")
    if file.content_type not in {
        "text/markdown",
        "text/plain",
        "application/octet-stream",
    }:
        raise HTTPException(415, "Only Markdown (.md) files are accepted")

    target = settings.data_dir / "incoming" / f"{uuid.uuid4()}.md"
    await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
    total = 0
    async with await open_file(target, "wb") as output:
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_source_file_size_mb * 1024 * 1024:
                await asyncio.to_thread(target.unlink, missing_ok=True)
                raise HTTPException(413, "Markdown exceeds configured size limit")
            await output.write(chunk)

    try:
        content = await asyncio.to_thread(target.read_text, encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        await asyncio.to_thread(target.unlink, missing_ok=True)
        raise HTTPException(422, "Markdown must be UTF-8 encoded") from exc
    if not content.strip():
        await asyncio.to_thread(target.unlink, missing_ok=True)
        raise HTTPException(422, "Markdown file is empty")

    job = await manager.submit(
        SourceKind.MARKDOWN,
        {"path": str(target), "name": filename, "bytes": total},
        {"language": language, "model": model, "template_id": template_id},
    )
    return JobAccepted(job_id=job.id)
