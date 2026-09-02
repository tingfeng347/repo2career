from __future__ import annotations

import asyncio
import shutil

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from repo2career.core.config import Settings, effective_settings, update_env
from repo2career.parsers.base import PdfParserKind
from repo2career.parsers.service import PdfParserService

router = APIRouter(tags=["settings"])


class SettingsUpdate(BaseModel):
    values: dict[str, str]


@router.get("/settings")
async def get_settings() -> dict:
    return {"settings": effective_settings()}


@router.put("/settings")
async def put_settings(request: SettingsUpdate) -> dict:
    try:
        await asyncio.to_thread(update_env, request.values)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"settings": effective_settings()}


@router.post("/settings/test-deepseek")
async def test_deepseek() -> dict:
    settings = Settings.load()
    if not settings.deepseek_api_key:
        raise HTTPException(422, "DEEPSEEK_API_KEY is not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{settings.deepseek_base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
        )
        response.raise_for_status()
    return {"ok": True, "model": settings.deepseek_model}


@router.post("/settings/test-mineru")
async def test_mineru() -> dict:
    settings = Settings.load()
    if not settings.mineru_api_key:
        return {"ok": True, "configured": False, "parser": "pypdf"}
    return {
        "ok": True,
        "configured": True,
        "parser": "mineru",
        "base_url": settings.mineru_base_url,
    }


@router.get("/capabilities")
async def capabilities() -> dict:
    settings = Settings.load()
    selected = PdfParserService(settings).selected(PdfParserKind.AUTO)
    return {
        "codegraph": {"available": bool(shutil.which("codegraph"))},
        "archify": {"available": bool(settings.archify_command)},
        "deepseek": {
            "configured": bool(settings.deepseek_api_key),
            "model": settings.deepseek_model,
        },
        "mineru": {"configured": bool(settings.mineru_api_key)},
        "pdf_parser": selected,
    }
