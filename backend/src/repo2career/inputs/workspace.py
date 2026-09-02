from __future__ import annotations

import asyncio
import shutil
import zipfile
from pathlib import Path, PurePosixPath

from anyio import open_file
from fastapi import UploadFile

from repo2career.core.config import Settings

EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "coverage",
    "__pycache__",
    ".idea",
    ".vscode",
}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
BINARY_SUFFIXES = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".jar",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".pdf",
}


def safe_relative_path(raw: str) -> Path:
    normalized = raw.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe relative path: {raw}")
    if ":" in path.parts[0]:
        raise ValueError(f"Drive-qualified paths are not accepted: {raw}")
    return Path(*path.parts)


def should_include(path: Path) -> bool:
    lowered = {part.lower() for part in path.parts}
    return not (
        lowered & EXCLUDED_PARTS
        or path.name.lower() in SECRET_NAMES
        or path.suffix.lower() in BINARY_SUFFIXES
        or path.is_symlink()
    )


def project_stats(root: Path, settings: Settings) -> dict[str, int]:
    count = 0
    total = 0
    max_total = settings.max_project_size_mb * 1024 * 1024
    max_file = settings.max_source_file_size_mb * 1024 * 1024
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root)
        if not should_include(relative):
            continue
        size = path.stat().st_size
        count += 1
        total += size
        if count > settings.max_project_files or size > max_file or total > max_total:
            raise ValueError("Repository exceeds configured limits")
    return {"accepted_files": count, "bytes": total}


async def save_uploads(
    files: list[UploadFile], paths: list[str], root: Path, settings: Settings
) -> dict[str, int]:
    if len(files) != len(paths):
        raise ValueError("Each uploaded file must have one relative path")
    if len(files) > settings.max_project_files:
        raise ValueError("Project file limit exceeded")
    await asyncio.to_thread(root.mkdir, parents=True, exist_ok=True)
    resolved_root = await asyncio.to_thread(root.resolve)
    total = 0
    accepted = 0
    max_total = settings.max_project_size_mb * 1024 * 1024
    max_file = settings.max_source_file_size_mb * 1024 * 1024
    for upload, raw_path in zip(files, paths, strict=True):
        relative = safe_relative_path(raw_path)
        if not should_include(relative):
            continue
        target = await asyncio.to_thread((root / relative).resolve)
        if resolved_root not in target.parents:
            raise ValueError("Upload escaped the workspace")
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        size = 0
        async with await open_file(target, "wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                total += len(chunk)
                if size > max_file or total > max_total:
                    await asyncio.to_thread(target.unlink, missing_ok=True)
                    raise ValueError("Project size limit exceeded")
                await output.write(chunk)
        accepted += 1
    return {"accepted_files": accepted, "bytes": total}


def extract_zip_safely(archive: Path, destination: Path, settings: Settings) -> dict[str, int]:
    count = 0
    total = 0
    max_total = settings.max_project_size_mb * 1024 * 1024
    max_file = settings.max_source_file_size_mb * 1024 * 1024
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            relative = safe_relative_path(member.filename)
            parts = relative.parts[1:] if len(relative.parts) > 1 else relative.parts
            relative = Path(*parts)
            if not parts or member.is_dir() or not should_include(relative):
                continue
            count += 1
            total += member.file_size
            if (
                count > settings.max_project_files
                or member.file_size > max_file
                or total > max_total
            ):
                raise ValueError("Repository archive exceeds configured limits")
            target = (destination / relative).resolve()
            if destination.resolve() not in target.parents:
                raise ValueError("Archive member escaped the workspace")
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    return {"accepted_files": count, "bytes": total}
