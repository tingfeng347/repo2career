from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlparse

from repo2career.core.config import Settings
from repo2career.inputs.workspace import project_stats

GITHUB_PATH = re.compile(r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("Only HTTPS GitHub repository URLs are supported")
    match = GITHUB_PATH.match(parsed.path)
    if not match:
        raise ValueError("Invalid GitHub repository URL")
    return match.group(1), match.group(2)


async def fetch_github_repository(
    url: str, ref: str | None, destination: Path, settings: Settings
) -> dict[str, str | int]:
    owner, repo = parse_github_url(url)
    if not shutil.which("git"):
        raise RuntimeError("Git is required to analyze GitHub repositories")

    clone_url = f"https://github.com/{owner}/{repo}.git"
    if settings.github_token:
        token = quote(settings.github_token, safe="")
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

    await asyncio.to_thread(destination.parent.mkdir, parents=True, exist_ok=True)
    if await asyncio.to_thread(destination.exists):
        await asyncio.to_thread(shutil.rmtree, destination)
    clone_args = ["clone", "--depth", "1", "--single-branch"]
    if ref:
        clone_args.extend(["--branch", ref])
    clone_args.extend([clone_url, str(destination)])
    await _run_git(*clone_args)
    revision = (await _run_git("-C", str(destination), "rev-parse", "HEAD")).strip()
    stats = await asyncio.to_thread(project_stats, destination, settings)
    return {"owner": owner, "repo": repo, "revision": revision, **stats}


async def _run_git(*args: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "git",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    if process.returncode:
        raise ValueError("Git operation failed. Verify repository access and the requested ref.")
    return stdout.decode("utf-8", errors="replace")
