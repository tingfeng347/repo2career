from __future__ import annotations

import hashlib
import json
from pathlib import Path

from repo2career.core.config import Settings
from repo2career.inputs.workspace import should_include
from repo2career.models.evidence import AnalysisEvidence, EvidenceRef

MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "pom.xml",
    "build.gradle",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
    "Dockerfile",
    "docker-compose.yml",
}
ENTRY_HINTS = {"main.py", "app.py", "server.py", "index.ts", "index.js", "main.go", "Program.cs"}
TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cs",
    ".php",
    ".rb",
    ".kt",
    ".sql",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".xml",
}


def scan_project(root: Path, settings: Settings, revision: str | None = None) -> AnalysisEvidence:
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and should_include(path.relative_to(root))
    ]
    files = sorted(files)[: settings.max_project_files]
    tree = [path.relative_to(root).as_posix() for path in files]
    refs: list[EvidenceRef] = []
    technologies: set[str] = set()
    warnings: list[str] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        if (
            path.name not in MANIFESTS
            and path.name not in ENTRY_HINTS
            and path.suffix.lower() not in TEXT_SUFFIXES
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            warnings.append(f"Unable to read {relative}: {exc}")
            continue
        if path.name == "package.json":
            technologies.update(_package_dependencies(text))
        elif path.name == "pyproject.toml":
            technologies.add("Python")
        elif path.name == "go.mod":
            technologies.add("Go")
        elif path.name == "Cargo.toml":
            technologies.add("Rust")
        elif path.name in {"Dockerfile", "docker-compose.yml"}:
            technologies.add("Docker")
        if path.name in MANIFESTS or path.name in ENTRY_HINTS:
            lines = text.splitlines()
            excerpt = "\n".join(lines[: min(80, len(lines))])
            digest = hashlib.sha1(relative.encode()).hexdigest()[:10]
            refs.append(
                EvidenceRef(
                    id=f"code-{digest}",
                    kind="code",
                    path=relative,
                    excerpt=excerpt,
                    start_line=1,
                    end_line=min(80, len(lines)),
                    revision=revision,
                    category="manifest" if path.name in MANIFESTS else "entrypoint",
                )
            )
    return AnalysisEvidence(
        project_name=root.name,
        source_summary=f"{len(files)} included files",
        technology=sorted(technologies),
        tree=tree,
        references=refs,
        warnings=warnings,
    )


def _package_dependencies(text: str) -> set[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"Node.js"}
    deps = set(data.get("dependencies", {})) | set(data.get("devDependencies", {}))
    result = {"Node.js"}
    mapping = {
        "react": "React",
        "vue": "Vue",
        "next": "Next.js",
        "vite": "Vite",
        "express": "Express",
    }
    for name, label in mapping.items():
        if name in deps:
            result.add(label)
    return result
