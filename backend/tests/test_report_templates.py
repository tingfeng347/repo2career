from pathlib import Path

import pytest

from repo2career.core.config import Settings
from repo2career.reports.templates import (
    DEFAULT_TEMPLATE_ID,
    ReportTemplateUpsert,
    delete_template,
    get_template,
    list_templates,
    save_template,
)


def test_builtin_template_matches_deep_dive_report_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    template = get_template(DEFAULT_TEMPLATE_ID, Settings.load())
    assert "## 一、项目概述与业务背景" in template.body
    assert "## 三、总体架构" in template.body
    assert "## 七、设计亮点与技术难点" in template.body
    assert "## 十、简历项目写法" in template.body
    assert "## 十一、面试问答要点" in template.body
    assert "基于仓库/文档证据" not in template.body
    assert "没有证据的数据不要猜测" not in template.body


def test_custom_template_can_be_saved_updated_and_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings = Settings.load()
    created = save_template(
        ReportTemplateUpsert(
            name="RAG 深挖",
            description="聚焦检索与问答链路",
            body=(
                "# {{project_name}}\n\n## 检索链路\n\n"
                "写清召回、融合、精排、降级、工程取舍和面试追问。"
            ),
        ),
        settings,
    )
    assert created.id.startswith("custom-")
    assert get_template(created.id, settings).name == "RAG 深挖"
    updated = save_template(
        ReportTemplateUpsert(
            id=created.id,
            name="RAG 深挖 V2",
            body=(
                "# {{project_name}}\n\n## 核心链路\n\n"
                "详细解释检索、融合、精排、容错、工程边界与面试追问。"
            ),
        ),
        settings,
    )
    assert updated.name == "RAG 深挖 V2"
    assert len(list_templates(settings)) == 2
    delete_template(created.id, settings)
    with pytest.raises(KeyError):
        get_template(created.id, settings)
