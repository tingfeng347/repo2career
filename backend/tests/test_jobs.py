from pathlib import Path

import pytest

from repo2career.db.jobs import JobRepository
from repo2career.models.domain import AnalysisStage, AnalysisStatus, SourceKind
from repo2career.services.jobs import JobManager


class FakeAnalysis:
    async def run(self, job, progress) -> None:
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
