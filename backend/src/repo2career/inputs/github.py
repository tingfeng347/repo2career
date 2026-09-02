from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from repo2career.core.config import Settings
from repo2career.inputs.workspace import extract_zip_safely

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
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    async with httpx.AsyncClient(headers=headers, timeout=120, follow_redirects=True) as client:
        metadata_response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        requested_ref = ref or metadata["default_branch"]
        commit_response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{requested_ref}"
        )
        commit_response.raise_for_status()
        revision = commit_response.json()["sha"]
        archive_response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/zipball/{revision}"
        )
        archive_response.raise_for_status()
        archive = destination.parent / "repository.zip"
        await asyncio.to_thread(archive.write_bytes, archive_response.content)
    stats = await asyncio.to_thread(extract_zip_safely, archive, destination, settings)
    await asyncio.to_thread(archive.unlink, missing_ok=True)
    return {"owner": owner, "repo": repo, "revision": revision, **stats}
