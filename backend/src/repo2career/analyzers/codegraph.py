from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

QUERIES = (
    "runtime entrypoints and system architecture",
    "complete business workflow and important call paths",
    "data persistence models repositories and migrations",
    "authentication authorization and external integrations",
)


async def analyze_with_codegraph(root: Path, timeout_seconds: int = 300) -> tuple[str, list[str]]:
    executable = shutil.which("codegraph")
    if not executable:
        return "", ["CodeGraph is not installed; deterministic scanning was used."]
    warnings: list[str] = []
    init = await _run(executable, "--no-color", "init", str(root), timeout_seconds=timeout_seconds)
    if init[0] != 0:
        return "", [f"CodeGraph indexing failed: {init[2][-500:]}"]
    sections = []
    for query in QUERIES:
        result = await _run(
            executable,
            "--no-color",
            "explore",
            query,
            "--path",
            str(root),
            timeout_seconds=timeout_seconds,
        )
        if result[0] == 0:
            sections.append(f"## {query}\n{result[1]}")
        else:
            warnings.append(f"CodeGraph query failed for {query}")
    return "\n\n".join(sections), warnings


async def _run(*args: str, timeout_seconds: int) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        async with asyncio.timeout(timeout_seconds):
            stdout, stderr = await process.communicate()
    except TimeoutError:
        process.kill()
        await process.wait()
        return 124, "", "Timed out"
    return process.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")
