from __future__ import annotations

import re
import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from repo2career.core.config import Settings

DEFAULT_TEMPLATE_ID = "career-deep-dive"
_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")

DEFAULT_TEMPLATE_BODY = """# {{project_name}} —— 项目深度分析与简历/面试要点

## 一、项目概述与业务背景

### 1.1 项目定位
### 1.2 业务要解决的问题
### 1.3 核心能力与使用入口
### 1.4 一句话介绍（面试开场）

---

## 二、技术栈与选型

先用 Markdown 表格按层次列出技术、用途和选型理由，再解释关键选型为什么这样做、替代方案和取舍。

---

## 三、总体架构

### 3.1 分层架构
使用 ```text 代码块画出清晰的 ASCII 架构图；按真实代码结构命名各层、服务和外部依赖。

### 3.2 模块职责
### 3.3 关键设计决策

---

## 四、核心功能与业务流程

按项目真实能力拆成 3~8 个三级标题。
每个功能说明：入口、关键类/函数、执行步骤、状态变化、异常/降级与业务价值。

---

## 五、核心调用链与数据流

挑最值得面试展开的 2~5 条链路，用 ```text 流程图逐步展开。
不要只写抽象描述，要尽量落到路由、服务、仓储、模型和外部系统。

---

## 六、核心数据模型、接口与状态

用表格或分组列表写清关键实体、状态机、持久化边界、主要 API / 事件协议。

---

## 七、设计亮点与技术难点（面试可讲）

围绕并发、可靠性、性能、可观测性、安全、数据一致性、可维护性、算法/检索策略等真实难点展开。
说明“问题 → 方案 → 为什么 → 代价”。

---

## 八、工程质量、安全与可靠性

说明测试、输入安全、敏感信息、失败恢复、超时/重试、资源限制和当前实现边界。

---

## 九、风险、证据缺口与可改进点

明确区分“源码已经实现”“设计上存在但证据不足”“建议未来演进”。不要把建议写成现状。

---

## 十、简历项目写法

### 版本 A：详细版
给出可直接放简历的项目名、技术栈和 4~6 条 bullet；只使用源码可证明的数据。
真实业务指标缺失时用【待补充：真实指标】标记。

### 版本 B：精简版
给出 3~4 条更短、更强调技术含量的 bullet。

---

## 十一、面试问答要点

给出 8~12 个高概率追问，问题使用 `### Q1：...` 格式，答案用引用块 `>`。
重点覆盖架构取舍、核心流程、故障场景、性能/并发、数据一致性和项目边界。

---

## 十二、面试使用建议

总结最值得讲的 3~5 个主题，以及哪些数字/业务结果需要候选人自行补充真实数据。
"""


class ReportTemplate(BaseModel):
    id: str
    name: str
    description: str = ""
    body: str
    builtin: bool = False


class ReportTemplateUpsert(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=240)
    body: str = Field(min_length=40, max_length=30000)


BUILTIN_TEMPLATE = ReportTemplate(
    id=DEFAULT_TEMPLATE_ID,
    name="项目深度分析与简历/面试要点",
    description="参考深度项目复盘文档：业务背景、架构、核心链路、技术难点、简历与面试问答。",
    body=DEFAULT_TEMPLATE_BODY,
    builtin=True,
)


def _template_dir(settings: Settings | None = None) -> Path:
    return (settings or Settings.load()).data_dir / "templates"


def list_templates(settings: Settings | None = None) -> list[ReportTemplate]:
    result = [BUILTIN_TEMPLATE]
    root = _template_dir(settings)
    if not root.is_dir():
        return result
    for path in sorted(root.glob("*.json")):
        try:
            item = ReportTemplate.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if item.id != DEFAULT_TEMPLATE_ID:
            result.append(item.model_copy(update={"builtin": False}))
    return result


def get_template(template_id: str | None, settings: Settings | None = None) -> ReportTemplate:
    wanted = template_id or DEFAULT_TEMPLATE_ID
    for template in list_templates(settings):
        if template.id == wanted:
            return template
    raise KeyError(wanted)


def save_template(
    request: ReportTemplateUpsert, settings: Settings | None = None
) -> ReportTemplate:
    template_id = request.id or f"custom-{uuid.uuid4().hex[:10]}"
    if template_id == DEFAULT_TEMPLATE_ID:
        raise ValueError("Built-in template cannot be overwritten")
    if not _ID_PATTERN.fullmatch(template_id):
        raise ValueError("Template id may contain only letters, numbers, '-' and '_'")
    template = ReportTemplate(
        id=template_id,
        name=request.name.strip(),
        description=request.description.strip(),
        body=request.body.strip(),
        builtin=False,
    )
    root = _template_dir(settings)
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{template_id}.json").write_text(
        template.model_dump_json(indent=2), encoding="utf-8"
    )
    return template


def delete_template(template_id: str, settings: Settings | None = None) -> None:
    if template_id == DEFAULT_TEMPLATE_ID:
        raise ValueError("Built-in template cannot be deleted")
    if not _ID_PATTERN.fullmatch(template_id):
        raise KeyError(template_id)
    target = _template_dir(settings) / f"{template_id}.json"
    if not target.is_file():
        raise KeyError(template_id)
    target.unlink()
