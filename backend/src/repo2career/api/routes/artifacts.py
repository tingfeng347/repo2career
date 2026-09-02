from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from repo2career.api.dependencies import job_repository
from repo2career.core.config import Settings
from repo2career.db.jobs import JobRepository

router = APIRouter(prefix="/analyses", tags=["artifacts"])


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
