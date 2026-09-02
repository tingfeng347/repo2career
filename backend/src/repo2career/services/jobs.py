from __future__ import annotations

import asyncio
import shutil
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from repo2career.core.config import Settings
from repo2career.db.jobs import JobRepository
from repo2career.models.domain import (
    AnalysisJob,
    AnalysisStage,
    AnalysisStatus,
    SourceKind,
    StageEvent,
)
from repo2career.services.analysis import AnalysisService


class JobManager:
    def __init__(
        self,
        repository: JobRepository,
        analysis: AnalysisService,
        data_dir: Path | None = None,
    ) -> None:
        self.repository = repository
        self.analysis = analysis
        self.data_dir = data_dir or Settings.load().data_dir
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.worker: asyncio.Task | None = None
        self.cancelled: set[str] = set()
        self.transient: dict[str, dict] = {}

    async def start(self) -> None:
        await self.repository.initialize()
        self.worker = asyncio.create_task(self._work(), name="repo2career-worker")

    async def stop(self) -> None:
        await self.queue.put(None)
        if self.worker:
            await self.worker

    async def submit(
        self,
        source_kind: SourceKind,
        source: dict,
        options: dict | None = None,
        transient: dict | None = None,
    ) -> AnalysisJob:
        job = AnalysisJob(
            id=str(uuid.uuid4()), source_kind=source_kind, source=source, options=options or {}
        )
        await self.repository.create(job)
        if transient:
            self.transient[job.id] = {f"_{key}": value for key, value in transient.items()}
        await self.repository.add_event(
            StageEvent(
                job_id=job.id, stage=AnalysisStage.QUEUED, progress=0, message="Analysis queued"
            )
        )
        await self.queue.put(job.id)
        return job

    async def retry(self, job_id: str) -> AnalysisJob:
        job = await self._required(job_id)
        if job.status not in {
            AnalysisStatus.FAILED,
            AnalysisStatus.INTERRUPTED,
            AnalysisStatus.CANCELLED,
        }:
            raise ValueError("Only failed, interrupted or cancelled jobs can be retried")
        await self.repository.update(
            job_id, status=AnalysisStatus.QUEUED, stage=AnalysisStage.QUEUED, progress=0, error=None
        )
        self.cancelled.discard(job_id)
        await self.queue.put(job_id)
        return await self._required(job_id)

    async def cancel(self, job_id: str) -> AnalysisJob:
        job = await self._required(job_id)
        if job.status in {
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        }:
            return job
        self.cancelled.add(job_id)
        await self.repository.update(
            job_id, status=AnalysisStatus.CANCELLED, error="Cancelled by user"
        )
        return await self._required(job_id)

    async def delete(self, job_id: str) -> None:
        job = await self._required(job_id)
        self.cancelled.add(job_id)
        self.transient.pop(job_id, None)

        incoming_root = await asyncio.to_thread((self.data_dir / "incoming").resolve)
        source_path = job.source.get("path")
        if isinstance(source_path, str):
            source = await asyncio.to_thread(Path(source_path).resolve)
            if source != incoming_root and incoming_root in source.parents:
                await asyncio.to_thread(self._remove_path, source)

        await asyncio.to_thread(self._remove_path, self.data_dir / "jobs" / job_id)
        await self.repository.delete(job_id)

    async def events(self, job_id: str, after_id: int = 0) -> AsyncIterator[StageEvent]:
        await self._required(job_id)
        cursor = after_id
        while True:
            events = await self.repository.events(job_id, cursor)
            for event in events:
                cursor = event.id or cursor
                yield event
            job = await self._required(job_id)
            if job.status in {
                AnalysisStatus.COMPLETED,
                AnalysisStatus.FAILED,
                AnalysisStatus.CANCELLED,
            }:
                return
            await asyncio.sleep(0.5)

    async def _work(self) -> None:
        while (job_id := await self.queue.get()) is not None:
            job = await self.repository.get(job_id)
            if not job:
                self.cancelled.discard(job_id)
                continue
            if job_id in self.cancelled:
                continue
            job.options.update(self.transient.pop(job_id, {}))
            await self.repository.update(job_id, status=AnalysisStatus.RUNNING, error=None)
            try:
                await self.analysis.run(
                    job,
                    lambda stage, progress, message: self._progress(
                        job_id, stage, progress, message
                    ),
                )
                if job_id not in self.cancelled and await self.repository.get(job_id):
                    await self._progress(job_id, AnalysisStage.COMPLETED, 100, "Analysis completed")
                    await self.repository.update(job_id, status=AnalysisStatus.COMPLETED)
            except asyncio.CancelledError:
                if job_id in self.cancelled:
                    if not await self.repository.get(job_id):
                        self.cancelled.discard(job_id)
                    continue
                await self.repository.update(
                    job_id, status=AnalysisStatus.INTERRUPTED, error="Worker stopped"
                )
                raise
            except Exception as exc:
                if await self.repository.get(job_id):
                    await self.repository.update(
                        job_id, status=AnalysisStatus.FAILED, error=str(exc)
                    )
                    await self.repository.add_event(
                        StageEvent(
                            job_id=job_id,
                            stage=job.stage,
                            progress=job.progress,
                            message=f"Analysis failed: {type(exc).__name__}: {exc}",
                        )
                    )

    async def _progress(
        self, job_id: str, stage: AnalysisStage, progress: int, message: str
    ) -> None:
        if job_id in self.cancelled:
            raise asyncio.CancelledError
        await self.repository.update(job_id, stage=stage, progress=progress)
        await self.repository.add_event(
            StageEvent(
                job_id=job_id,
                stage=stage,
                progress=progress,
                message=message,
                created_at=datetime.now(UTC),
            )
        )

    async def _required(self, job_id: str) -> AnalysisJob:
        job = await self.repository.get(job_id)
        if not job:
            raise KeyError(job_id)
        return job

    @staticmethod
    def _remove_path(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
