import asyncio
import shutil
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from repo2career.api.routes.analyses import analyze_local_folder
from repo2career.core.config import Settings
from repo2career.inputs import github
from repo2career.inputs.github import fetch_github_repository, parse_github_url
from repo2career.inputs.workspace import (
    project_stats,
    remove_path,
    safe_relative_path,
    should_include,
)
from repo2career.models.domain import LocalFolderAnalysisRequest, SourceKind


@pytest.mark.parametrize("value", ["../secret", "/absolute", "C:/Windows/file"])
def test_rejects_unsafe_relative_paths(value: str) -> None:
    with pytest.raises(ValueError):
        safe_relative_path(value)


def test_excludes_secrets_and_dependencies() -> None:
    assert not should_include(Path("project/.env"))
    assert not should_include(Path("project/node_modules/pkg/index.js"))
    assert should_include(Path("project/src/main.py"))


def test_parses_only_https_github_urls() -> None:
    assert parse_github_url("https://github.com/openai/openai-python") == (
        "openai",
        "openai-python",
    )
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/openai/openai-python")


def test_project_stats_enforces_source_limits(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')")
    (tmp_path / ".env").write_text("SECRET=not-counted")
    settings = replace(
        Settings.load(), max_project_files=1, max_project_size_mb=1, max_source_file_size_mb=1
    )

    assert project_stats(tmp_path, settings) == {"accepted_files": 1, "bytes": 11}
    (tmp_path / "src" / "other.py").write_text("pass")
    with pytest.raises(ValueError, match="Repository exceeds configured limits"):
        project_stats(tmp_path, settings)


def test_remove_path_retries_windows_style_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "source"
    target.mkdir()
    (target / "pack.idx").write_text("pack")
    real_rmtree = shutil.rmtree
    calls = 0

    def flaky_rmtree(path, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError(5, "Access denied", str(target / "pack.idx"))
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr("repo2career.inputs.workspace.shutil.rmtree", flaky_rmtree)
    remove_path(target, delay=0)

    assert calls == 2
    assert not target.exists()


@pytest.mark.asyncio
async def test_local_folder_route_uses_existing_directory_without_copy(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class Manager:
        async def submit(self, kind, source, options):
            captured.update(kind=kind, source=source, options=options)
            return SimpleNamespace(id="local-folder-job")

    result = await analyze_local_folder(
        LocalFolderAnalysisRequest(path=str(tmp_path), language="en"), Manager()
    )

    assert result.job_id == "local-folder-job"
    assert captured == {
        "kind": SourceKind.FOLDER,
        "source": {"path": str(tmp_path), "name": tmp_path.name},
        "options": {"language": "en", "model": None, "template_id": "career-deep-dive"},
    }


@pytest.mark.asyncio
async def test_local_folder_route_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(HTTPException, match="Local folder does not exist"):
        await analyze_local_folder(
            LocalFolderAnalysisRequest(path=str(tmp_path / "missing")), SimpleNamespace()
        )


@pytest.mark.asyncio
async def test_github_repository_uses_shallow_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[tuple[str, ...]] = []

    def create_clone(destination: Path) -> None:
        destination.mkdir(parents=True)
        (destination / "src").mkdir()
        (destination / "src" / "main.py").write_text("print('ok')")

    async def run_git(*args: str) -> str:
        commands.append(args)
        if args[0] == "clone":
            destination = Path(args[-1])
            await asyncio.to_thread(create_clone, destination)
            return ""
        return "abc123\n"

    monkeypatch.setattr(github.shutil, "which", lambda _: "/usr/bin/git")
    monkeypatch.setattr(github, "_run_git", run_git)
    settings = replace(Settings.load(), max_project_size_mb=1, max_source_file_size_mb=1)

    metadata = await fetch_github_repository(
        "https://github.com/openai/openai-python", "main", tmp_path / "source", settings
    )

    assert commands[0] == (
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--branch",
        "main",
        "https://github.com/openai/openai-python.git",
        str(tmp_path / "source"),
    )
    assert commands[1] == ("-C", str(tmp_path / "source"), "rev-parse", "HEAD")
    assert metadata == {
        "owner": "openai",
        "repo": "openai-python",
        "revision": "abc123",
        "accepted_files": 1,
        "bytes": 11,
    }
