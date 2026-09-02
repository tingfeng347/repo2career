from __future__ import annotations

import asyncio
import json
import os
import shlex
from pathlib import Path

from repo2career.core.config import Settings
from repo2career.reports.schema import ReportContent


def split_command(command: str, *, platform: str | None = None) -> list[str]:
    platform = platform or os.name
    posix = platform != "nt"
    args = shlex.split(command, posix=posix)
    if posix:
        return args
    return [
        argument[1:-1] if len(argument) >= 2 and argument[0] == argument[-1] == '"' else argument
        for argument in args
    ]


async def render_archify(
    content: ReportContent, output: Path, settings: Settings
) -> tuple[bool, str | None]:
    ir = {
        "title": f"{content.project_name} Architecture",
        "nodes": [
            {"id": "user", "label": "User", "kind": "actor"},
            {"id": "application", "label": content.project_name, "kind": "system"},
            {"id": "data", "label": "Data & Integrations", "kind": "boundary"},
        ],
        "edges": [
            {"from": "user", "to": "application", "label": "uses"},
            {"from": "application", "to": "data", "label": "reads/writes"},
        ],
    }
    ir_path = output / "assets" / "architecture.ir.json"
    await asyncio.to_thread(ir_path.parent.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(
        ir_path.write_text, json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not settings.archify_command:
        return False, "Archify command is not configured; Mermaid source was generated."
    command = settings.archify_command.format(
        input=str(ir_path), output=str(output / "assets" / "architecture.svg")
    )
    args = split_command(command)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode:
        return False, f"Archify failed: {stderr.decode(errors='replace')[-500:]}"
    return True, None
