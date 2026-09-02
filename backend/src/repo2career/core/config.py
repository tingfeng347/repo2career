from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Final

from dotenv import dotenv_values, set_key

SECRET_KEYS: Final = {"DEEPSEEK_API_KEY", "MINERU_API_KEY", "GITHUB_TOKEN"}
EDITABLE_KEYS: Final = SECRET_KEYS | {
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_REASONING_EFFORT",
    "MINERU_BASE_URL",
    "PDF_PARSER",
    "DATA_DIR",
    "MAX_PDF_SIZE_MB",
    "MAX_PROJECT_FILES",
    "MAX_PROJECT_SIZE_MB",
    "MAX_SOURCE_FILE_SIZE_MB",
    "ARCHIFY_COMMAND",
    "FRONTEND_ORIGIN",
}
_ENV_LOCK = Lock()
_SYSTEM_ENV_KEYS = frozenset(os.environ)


def project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def env_path() -> Path:
    return project_root() / ".env"


def _value(name: str, default: str = "") -> str:
    file_value = dotenv_values(env_path()).get(name)
    return os.environ.get(name, file_value if file_value is not None else default).strip()


@dataclass(frozen=True, slots=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    deepseek_reasoning_effort: str
    mineru_api_key: str
    mineru_base_url: str
    pdf_parser: str
    github_token: str
    data_dir: Path
    max_pdf_size_mb: int
    max_project_files: int
    max_project_size_mb: int
    max_source_file_size_mb: int
    archify_command: str
    frontend_origin: str

    @classmethod
    def load(cls) -> Settings:
        root = project_root()
        data = Path(_value("DATA_DIR", ".data"))
        if not data.is_absolute():
            data = root / data
        return cls(
            deepseek_api_key=_value("DEEPSEEK_API_KEY"),
            deepseek_base_url=_value("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            deepseek_model=_value("DEEPSEEK_MODEL", "deepseek-v4-pro"),
            deepseek_reasoning_effort=_value("DEEPSEEK_REASONING_EFFORT", "high"),
            mineru_api_key=_value("MINERU_API_KEY"),
            mineru_base_url=_value("MINERU_BASE_URL", "https://mineru.net"),
            pdf_parser=_value("PDF_PARSER", "auto"),
            github_token=_value("GITHUB_TOKEN"),
            data_dir=data.resolve(),
            max_pdf_size_mb=int(_value("MAX_PDF_SIZE_MB", "200")),
            max_project_files=int(_value("MAX_PROJECT_FILES", "20000")),
            max_project_size_mb=int(_value("MAX_PROJECT_SIZE_MB", "1024")),
            max_source_file_size_mb=int(_value("MAX_SOURCE_FILE_SIZE_MB", "5")),
            archify_command=_value("ARCHIFY_COMMAND"),
            frontend_origin=_value("FRONTEND_ORIGIN", "http://localhost:5173"),
        )


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:3]}{'*' * 8}{value[-3:]}"


def effective_settings() -> list[dict[str, str | bool]]:
    file_values = dotenv_values(env_path())
    defaults = Settings.load()
    mapping = {
        "DEEPSEEK_API_KEY": defaults.deepseek_api_key,
        "DEEPSEEK_BASE_URL": defaults.deepseek_base_url,
        "DEEPSEEK_MODEL": defaults.deepseek_model,
        "DEEPSEEK_REASONING_EFFORT": defaults.deepseek_reasoning_effort,
        "MINERU_API_KEY": defaults.mineru_api_key,
        "MINERU_BASE_URL": defaults.mineru_base_url,
        "PDF_PARSER": defaults.pdf_parser,
        "GITHUB_TOKEN": defaults.github_token,
    }
    result = []
    for key, value in mapping.items():
        source = (
            "environment"
            if key in _SYSTEM_ENV_KEYS
            else ".env"
            if key in file_values
            else "default"
        )
        result.append(
            {
                "key": key,
                "value": mask(value) if key in SECRET_KEYS else value,
                "source": source,
                "secret": key in SECRET_KEYS,
                "configured": bool(value),
            }
        )
    return result


def update_env(values: dict[str, str]) -> None:
    unknown = set(values) - EDITABLE_KEYS
    if unknown:
        raise ValueError(f"Unsupported settings: {', '.join(sorted(unknown))}")
    path = env_path()
    with _ENV_LOCK:
        path.touch(exist_ok=True)
        temp = path.with_suffix(".env.tmp")
        shutil.copyfile(path, temp)
        try:
            for key, value in values.items():
                set_key(temp, key, str(value), quote_mode="always", encoding="utf-8")
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    for key, value in values.items():
        if key not in _SYSTEM_ENV_KEYS:
            os.environ[key] = str(value)
