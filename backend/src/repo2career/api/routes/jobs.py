from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from repo2career.api.dependencies import job_manager, job_repository
from repo2career.db.jobs import JobRepository
from repo2career.models.domain import AnalysisJob
from repo2career.services.jobs import JobManager

router = APIRouter(prefix="/analyses", tags=["jobs"])


@router.get("", response_model=list[AnalysisJob])
async def list_jobs(
    repository: Annotated[JobRepository, Depends(job_repository)],
) -> list[AnalysisJob]:
    return await repository.list()


@router.get("/{job_id}", response_model=AnalysisJob)
async def get_job(
    job_id: str, repository: Annotated[JobRepository, Depends(job_repository)]
) -> AnalysisJob:
    job = await repository.get(job_id)
    if not job:
        raise HTTPException(404, "Analysis job not found")
    return job


@router.delete("/{job_id}")
async def delete_job(
    job_id: str, manager: Annotated[JobManager, Depends(job_manager)]
) -> dict[str, str]:
    try:
        await manager.delete(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Analysis job not found") from exc
    return {"job_id": job_id}


@router.get("/{job_id}/events")
async def stream_events(
    job_id: str,
    manager: Annotated[JobManager, Depends(job_manager)],
    after: int = Query(default=0, ge=0),
) -> StreamingResponse:
    async def generate():
        try:
            async for event in manager.events(job_id, after):
                yield f"id: {event.id}\nevent: progress\ndata: {event.model_dump_json()}\n\n"
        except KeyError:
            yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{job_id}/cancel", response_model=AnalysisJob)
async def cancel_job(
    job_id: str, manager: Annotated[JobManager, Depends(job_manager)]
) -> AnalysisJob:
    try:
        return await manager.cancel(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Analysis job not found") from exc


@router.post("/{job_id}/retry", response_model=AnalysisJob)
async def retry_job(
    job_id: str, manager: Annotated[JobManager, Depends(job_manager)]
) -> AnalysisJob:
    try:
        return await manager.retry(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Analysis job not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
