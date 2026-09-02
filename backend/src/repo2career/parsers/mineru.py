from __future__ import annotations

import asyncio
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import httpx

from repo2career.core.config import Settings
from repo2career.parsers.base import ParsedDocument, ParsedPage, PdfParserKind


class MineruCloudParser:
    def __init__(self, settings: Settings, timeout: int = 900) -> None:
        self.settings = settings
        self.timeout = timeout

    async def parse(self, path: Path, password: str | None = None) -> ParsedDocument:
        if password:
            raise ValueError("MinerU cloud mode does not accept local PDF passwords")
        if not self.settings.mineru_api_key:
            raise ValueError("MINERU_API_KEY is not configured")
        headers = {"Authorization": f"Bearer {self.settings.mineru_api_key}"}
        base = self.settings.mineru_base_url.rstrip("/")
        async with httpx.AsyncClient(headers=headers, timeout=120, follow_redirects=True) as client:
            response = await client.post(
                f"{base}/api/v4/file-urls/batch",
                json={"files": [{"name": path.name, "data_id": path.stem}], "model_version": "vlm"},
            )
            data = self._payload(response)
            batch_id = data["batch_id"]
            upload_url = data["file_urls"][0]
            # Presigned MinerU URLs must not receive an injected Content-Type header.
            file_content = await asyncio.to_thread(path.read_bytes)
            upload = await client.put(upload_url, content=file_content)
            upload.raise_for_status()
            result = await self._poll(client, base, batch_id)
            result_url = (
                result.get("full_zip_url") or result.get("zip_url") or result.get("markdown_url")
            )
            if not result_url:
                raise RuntimeError("MinerU completed without a downloadable result")
            downloaded = await client.get(result_url)
            downloaded.raise_for_status()
        markdown, pages = self._read_result(downloaded.content, result_url)
        warnings = []
        if len(pages) == 1 and pages[0].text == markdown:
            warnings.append(
                "MinerU result did not expose page boundaries; evidence is page 1 only."
            )
        return ParsedDocument(
            filename=path.name,
            parser=PdfParserKind.MINERU,
            pages=pages,
            markdown=markdown,
            warnings=warnings,
            remote_task_id=batch_id,
        )

    async def _poll(self, client: httpx.AsyncClient, base: str, batch_id: str) -> dict:
        deadline = asyncio.get_running_loop().time() + self.timeout
        while asyncio.get_running_loop().time() < deadline:
            response = await client.get(f"{base}/api/v4/extract-results/batch/{batch_id}")
            data = self._payload(response)
            items = data.get("extract_result") or data.get("extract_results") or []
            if isinstance(items, dict):
                items = [items]
            if items:
                item = items[0]
                state = str(item.get("state", item.get("status", ""))).lower()
                if state in {"done", "completed", "success"}:
                    return item
                if state in {"failed", "error"}:
                    raise RuntimeError(
                        item.get("err_msg") or item.get("message") or "MinerU parsing failed"
                    )
            await asyncio.sleep(2)
        raise TimeoutError("MinerU parsing timed out")

    @staticmethod
    def _payload(response: httpx.Response) -> dict:
        if response.status_code == 401:
            raise RuntimeError(
                "MinerU 鉴权失败（401）：请在 API 管理页面创建 API Token，"
                "不要使用网页登录 JWT。"
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(payload.get("msg") or "MinerU request failed")
        return payload.get("data") or {}

    @staticmethod
    def _read_result(content: bytes, url: str) -> tuple[str, list[ParsedPage]]:
        if url.lower().endswith(".zip") or content.startswith(b"PK"):
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = [name for name in archive.namelist() if name.lower().endswith(".md")]
                if not names:
                    raise RuntimeError("MinerU result archive contains no Markdown")
                markdown = archive.read(sorted(names, key=len)[0]).decode("utf-8", errors="replace")
                content_lists = [
                    name
                    for name in archive.namelist()
                    if name.lower().endswith("content_list.json")
                ]
                if content_lists:
                    payload = json.loads(archive.read(content_lists[0]))
                    pages = MineruCloudParser._content_pages(payload)
                    if pages:
                        return markdown, pages
                return markdown, MineruCloudParser._pages(markdown)
        markdown = content.decode("utf-8", errors="replace")
        return markdown, MineruCloudParser._pages(markdown)

    @staticmethod
    def _content_pages(payload: object) -> list[ParsedPage]:
        if not isinstance(payload, list):
            return []
        grouped: dict[int, list[str]] = defaultdict(list)
        for item in payload:
            if not isinstance(item, dict):
                continue
            page_index = item.get("page_idx", item.get("page_no", item.get("page", 0)))
            text = item.get("text") or item.get("content")
            if isinstance(text, str) and text.strip():
                grouped[int(page_index) + 1].append(text.strip())
        return [
            ParsedPage(number=number, text="\n\n".join(parts))
            for number, parts in sorted(grouped.items())
        ]

    @staticmethod
    def _pages(markdown: str) -> list[ParsedPage]:
        return [ParsedPage(number=1, text=markdown)]
