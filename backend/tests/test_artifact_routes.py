from pathlib import Path

import pytest
from fastapi import HTTPException

from repo2career.api.routes.artifacts import code_source_file
from repo2career.db.jobs import JobRepository
from repo2career.models.domain import AnalysisJob, SourceKind


async def folder_repository(tmp_path: Path, source_root: Path) -> JobRepository:
    repository = JobRepository(tmp_path / "jobs.db")
    await repository.initialize()
    await repository.create(
        AnalysisJob(
            id="folder-job",
            source_kind=SourceKind.FOLDER,
            source={"path": str(source_root)},
        )
    )
    return repository


@pytest.mark.asyncio
async def test_code_source_file_reads_a_file_inside_the_project(tmp_path: Path) -> None:
    source_root = tmp_path / "project"
    source_root.mkdir()
    (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")
    repository = await folder_repository(tmp_path, source_root)

    result = await code_source_file("folder-job", "main.py", repository)

    assert result == {"path": "main.py", "content": "print('ok')\n"}


@pytest.mark.asyncio
async def test_code_source_file_rejects_path_traversal(tmp_path: Path) -> None:
    source_root = tmp_path / "project"
    source_root.mkdir()
    repository = await folder_repository(tmp_path, source_root)

    with pytest.raises(HTTPException) as error:
        await code_source_file("folder-job", "../secret.txt", repository)

    assert error.value.status_code == 400
