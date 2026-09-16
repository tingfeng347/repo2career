from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from repo2career.api.routes import analyses, artifacts, jobs, settings, templates
from repo2career.core.config import Settings, project_root
from repo2career.db.jobs import JobRepository
from repo2career.services.analysis import AnalysisService
from repo2career.services.jobs import JobManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = Settings.load()
    repository = JobRepository(config.data_dir / "repo2career.db")
    manager = JobManager(repository, AnalysisService())
    app.state.job_repository = repository
    app.state.job_manager = manager
    await manager.start()
    try:
        yield
    finally:
        await manager.stop()


def create_app() -> FastAPI:
    config = Settings.load()
    app = FastAPI(
        title="Repo2Career API",
        version="0.1.0",
        description="Evidence-first repository and PDF analysis",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "repo2career"}

    app.include_router(analyses.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(artifacts.router, prefix="/api/v1")
    app.include_router(settings.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")
    frontend = project_root() / "frontend" / "dist"
    if frontend.is_dir() and hasattr(app, "frontend"):
        app.frontend("/", directory=frontend)
    return app


app = create_app()
