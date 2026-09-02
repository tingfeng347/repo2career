from pathlib import Path

import pytest

import repo2career.core.config as config


def test_settings_mask_and_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / ".env"
    monkeypatch.setattr(config, "env_path", lambda: target)
    config.update_env({"DEEPSEEK_API_KEY": "secret-value-123"})
    rows = {row["key"]: row for row in config.effective_settings()}
    assert "secret-value-123" not in str(rows["DEEPSEEK_API_KEY"])
    with pytest.raises(ValueError):
        config.update_env({"UNSAFE_KEY": "value"})
