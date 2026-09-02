from pathlib import Path

import pytest

from repo2career.inputs.github import parse_github_url
from repo2career.inputs.workspace import safe_relative_path, should_include


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
