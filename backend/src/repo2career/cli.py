from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from pathlib import Path
from typing import Annotated

import typer

from repo2career.core.config import Settings, effective_settings, update_env
from repo2career.db.jobs import JobRepository
from repo2career.inputs.github import parse_github_url
from repo2career.inputs.workspace import should_include
from repo2career.models.domain import AnalysisStatus, SourceKind
from repo2career.parsers.base import PdfParserKind
from repo2career.services.analysis import AnalysisService
from repo2career.services.jobs import JobManager

app = typer.Typer(help="Turn repositories and project PDFs into evidence-first career reports.")
analyze_app = typer.Typer(help="Analyze a source")
app.add_typer(analyze_app, name="analyze")


async def _manager() -> JobManager:
    settings = Settings.load()
    manager = JobManager(JobRepository(settings.data_dir / "repo2career.db"), AnalysisService())
    await manager.start()
    return manager


async def _wait(manager: JobManager, job_id: str) -> Path:
    async for event in manager.events(job_id):
        typer.echo(f"[{event.progress:3d}%] {event.stage}: {event.message}")
    job = await manager.repository.get(job_id)
    await manager.stop()
    if not job or job.status != AnalysisStatus.COMPLETED:
        raise typer.Exit(code=1)
    path = Settings.load().data_dir / "jobs" / job_id / "report" / "report.md"
    typer.echo(f"Report: {path}")
    return path


@analyze_app.command("github")
def analyze_github(
    url: str,
    ref: Annotated[str | None, typer.Option()] = None,
    language: Annotated[str, typer.Option()] = "zh-CN",
    model: Annotated[str | None, typer.Option()] = None,
) -> None:
    async def run() -> None:
        parse_github_url(url)
        manager = await _manager()
        job = await manager.submit(
            SourceKind.GITHUB,
            {"repository_url": url, "ref": ref},
            {"language": language, "model": model},
        )
        await _wait(manager, job.id)

    asyncio.run(run())


@analyze_app.command("folder")
def analyze_folder(
    path: Path,
    language: Annotated[str, typer.Option()] = "zh-CN",
    model: Annotated[str | None, typer.Option()] = None,
) -> None:
    source = path.resolve()
    if not source.is_dir():
        raise typer.BadParameter("Folder does not exist")

    async def run() -> None:
        settings = Settings.load()
        snapshot = settings.data_dir / "incoming" / str(uuid.uuid4())

        def copy() -> None:
            for item in source.rglob("*"):
                relative = item.relative_to(source)
                if not item.is_file() or not should_include(relative):
                    continue
                target = snapshot / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

        await asyncio.to_thread(copy)
        manager = await _manager()
        job = await manager.submit(
            SourceKind.FOLDER,
            {"path": str(snapshot), "name": source.name},
            {"language": language, "model": model},
        )
        await _wait(manager, job.id)

    asyncio.run(run())


@analyze_app.command("pdf")
def analyze_pdf(
    path: Path,
    parser: Annotated[PdfParserKind, typer.Option()] = PdfParserKind.AUTO,
    language: Annotated[str, typer.Option()] = "zh-CN",
    model: Annotated[str | None, typer.Option()] = None,
    password: Annotated[str | None, typer.Option(prompt=False, hide_input=True)] = None,
) -> None:
    source = path.resolve()
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise typer.BadParameter("PDF does not exist")

    async def run() -> None:
        manager = await _manager()
        job = await manager.submit(
            SourceKind.PDF,
            {"path": str(source), "name": source.name},
            {"language": language, "model": model, "parser": parser},
            {"password": password} if password else None,
        )
        await _wait(manager, job.id)

    asyncio.run(run())


@app.command("jobs")
def list_jobs() -> None:
    async def run() -> None:
        manager = await _manager()
        for job in await manager.repository.list():
            typer.echo(f"{job.id}  {job.status:11}  {job.source_kind:7}  {job.progress:3d}%")
        await manager.stop()

    asyncio.run(run())


@app.command("retry")
def retry(job_id: str) -> None:
    async def run() -> None:
        manager = await _manager()
        await manager.retry(job_id)
        await _wait(manager, job_id)

    asyncio.run(run())


@app.command("report")
def report(job_id: str) -> None:
    path = Settings.load().data_dir / "jobs" / job_id / "report" / "report.md"
    if not path.is_file():
        raise typer.BadParameter("Report is not ready")
    typer.echo(path)


@app.command("config")
def config(
    key: Annotated[str | None, typer.Option()] = None,
    value: Annotated[str | None, typer.Option()] = None,
) -> None:
    if key:
        if value is None:
            raise typer.BadParameter("--value is required with --key")
        update_env({key: value})
    typer.echo(json.dumps(effective_settings(), ensure_ascii=False, indent=2))


@app.command("doctor")
def doctor() -> None:
    settings = Settings.load()
    typer.echo(
        f"CodeGraph: {'ready' if shutil.which('codegraph') else 'missing (fallback enabled)'}"
    )
    typer.echo(f"DeepSeek: {'configured' if settings.deepseek_api_key else 'missing API key'}")
    typer.echo(f"PDF auto parser: {'mineru' if settings.mineru_api_key else 'pypdf'}")
    typer.echo(
        f"Archify: {'configured' if settings.archify_command else 'missing (Mermaid fallback)'}"
    )


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("repo2career.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
