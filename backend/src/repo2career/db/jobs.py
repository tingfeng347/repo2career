from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from repo2career.models.domain import (
    AnalysisJob,
    AnalysisStage,
    AnalysisStatus,
    SourceKind,
    StageEvent,
)


class JobRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        await asyncio.to_thread(self.path.parent.mkdir, parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    source_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    source_json TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                );
                """
            )
            await db.execute(
                "UPDATE jobs SET status=?, error=?, updated_at=? WHERE status=?",
                (
                    AnalysisStatus.INTERRUPTED,
                    "Application restarted while analysis was running",
                    datetime.now(UTC).isoformat(),
                    AnalysisStatus.RUNNING,
                ),
            )
            await db.commit()

    async def create(self, job: AnalysisJob) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.id,
                    job.source_kind,
                    job.status,
                    job.stage,
                    job.progress,
                    json.dumps(job.source, ensure_ascii=False),
                    json.dumps(job.options, ensure_ascii=False),
                    job.error,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )
            await db.commit()

    async def get(self, job_id: str) -> AnalysisJob | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute("SELECT * FROM jobs WHERE id=?", (job_id,))).fetchone()
        return self._job(row) if row else None

    async def list(self, limit: int = 100) -> list[AnalysisJob]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            ).fetchall()
        return [self._job(row) for row in rows]

    async def delete(self, job_id: str) -> bool:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM events WHERE job_id=?", (job_id,))
            cursor = await db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            await db.commit()
        return cursor.rowcount > 0

    async def update(
        self,
        job_id: str,
        *,
        status: AnalysisStatus | None = None,
        stage: AnalysisStage | None = None,
        progress: int | None = None,
        error: str | None = None,
    ) -> None:
        current = await self.get(job_id)
        if not current:
            raise KeyError(job_id)
        await self._update_values(
            job_id,
            status or current.status,
            stage or current.stage,
            current.progress if progress is None else progress,
            error,
        )

    async def _update_values(
        self,
        job_id: str,
        status: AnalysisStatus,
        stage: AnalysisStage,
        progress: int,
        error: str | None,
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE jobs SET status=?, stage=?, progress=?, error=?, updated_at=? WHERE id=?",
                (status, stage, progress, error, datetime.now(UTC).isoformat(), job_id),
            )
            await db.commit()

    async def add_event(self, event: StageEvent) -> StageEvent:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO events(job_id, stage, progress, message, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    event.job_id,
                    event.stage,
                    event.progress,
                    event.message,
                    event.created_at.isoformat(),
                ),
            )
            await db.commit()
            event.id = cursor.lastrowid
        return event

    async def events(self, job_id: str, after_id: int = 0) -> list[StageEvent]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    "SELECT * FROM events WHERE job_id=? AND id>? ORDER BY id", (job_id, after_id)
                )
            ).fetchall()
        return [
            StageEvent(
                id=row["id"],
                job_id=row["job_id"],
                stage=row["stage"],
                progress=row["progress"],
                message=row["message"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def _job(row: aiosqlite.Row) -> AnalysisJob:
        return AnalysisJob(
            id=row["id"],
            source_kind=SourceKind(row["source_kind"]),
            status=AnalysisStatus(row["status"]),
            stage=AnalysisStage(row["stage"]),
            progress=row["progress"],
            source=json.loads(row["source_json"]),
            options=json.loads(row["options_json"]),
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
