from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from repo2career.reports.templates import (
    ReportTemplate,
    ReportTemplateUpsert,
    delete_template,
    list_templates,
    save_template,
)

router = APIRouter(prefix="/report-templates", tags=["report-templates"])


@router.get("", response_model=list[ReportTemplate])
async def templates() -> list[ReportTemplate]:
    return list_templates()


@router.post("", response_model=ReportTemplate, status_code=status.HTTP_201_CREATED)
async def upsert_template(request: ReportTemplateUpsert) -> ReportTemplate:
    try:
        return save_template(request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.delete("/{template_id}")
async def remove_template(template_id: str) -> dict[str, str]:
    try:
        delete_template(template_id)
    except KeyError as exc:
        raise HTTPException(404, "Report template not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"template_id": template_id}
