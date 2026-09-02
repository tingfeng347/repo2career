import asyncio
from pathlib import Path

import pytest

from repo2career.db.jobs import JobRepository
from repo2career.models.domain import AnalysisStage, AnalysisStatus, SourceKind
from repo2career.services.jobs import JobManager


class FakeAnalysis:
    async def run(self, job, progress) -> None:
        await progress(AnalysisStage.ANALYZING, 50, "testing")


class PausingAnalysis:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def run(self, job, progress) -> None:
        self.started.set()
        await self.release.wait()
        await progress(AnalysisStage.ANALYZING, 50, "testing")


@pytest.mark.asyncio
async def test_job_lifecycle_is_durable(tmp_path: Path) -> None:
    repository = JobRepository(tmp_path / "jobs.db")
    manager = JobManager(repository, FakeAnalysis())
    await manager.start()
    job = await manager.submit(SourceKind.FOLDER, {"path": str(tmp_path)})
    async for _ in manager.events(job.id):
        pass
    completed = await repository.get(job.id)
    assert completed and completed.status == AnalysisStatus.COMPLETED
    assert completed.progress == 100
    await manager.stop()


@pytest.mark.asyncio
async def test_delete_job_removes_records_and_owned_files(tmp_path: Path) -> None:
    repository = JobRepository(tmp_path / "repo2career.db")
    await repository.initialize()
    manager = JobManager(repository, FakeAnalysis(), data_dir=tmp_path)

    source = tmp_path / "incoming" / "source.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-test")
    job = await manager.submit(SourceKind.PDF, {"path": str(source), "name": "source.pdf"})
    generated_report = tmp_path / "jobs" / job.id / "report" / "report.md"
    generated_report.parent.mkdir(parents=True)
    generated_report.write_text("report")

    await manager.delete(job.id)

    assert await repository.get(job.id) is None
    assert await repository.events(job.id) == []
    assert not source.exists()
    assert not generated_report.parent.parent.exists()

    await manager.start()
    await manager.stop()


@pytest.mark.asyncio
async def test_delete_running_job_keeps_worker_available(tmp_path: Path) -> None:
    repository = JobRepository(tmp_path / "repo2career.db")
    analysis = PausingAnalysis()
    manager = JobManager(repository, analysis, data_dir=tmp_path)
    await manager.start()

    deleted = await manager.submit(SourceKind.FOLDER, {"path": str(tmp_path / "external")})
    await analysis.started.wait()
    await manager.delete(deleted.id)
    analysis.release.set()

    replacement = await manager.submit(SourceKind.FOLDER, {"path": str(tmp_path / "external")})
    async for _ in manager.events(replacement.id):
        pass

    completed = await repository.get(replacement.id)
    assert completed and completed.status == AnalysisStatus.COMPLETED
    assert await repository.get(deleted.id) is None
    await manager.stop()
