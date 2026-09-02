from fastapi import Request

from repo2career.db.jobs import JobRepository
from repo2career.services.jobs import JobManager


def job_manager(request: Request) -> JobManager:
    return request.app.state.job_manager


def job_repository(request: Request) -> JobRepository:
    return request.app.state.job_repository
