from __future__ import annotations

import asyncio
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import httpx

from repo2career.core.config import Settings
from repo2career.parsers.base import ParsedBlock, ParsedDocument, ParsedPage, PdfParserKind


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
                middle_files = [
                    name for name in archive.namelist() if name.lower().endswith("_middle.json")
                ]
                if middle_files:
                    payload = json.loads(archive.read(middle_files[0]))
                    pages = MineruCloudParser._middle_pages(payload)
                    if pages:
                        return markdown, pages
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
    def _middle_pages(payload: object) -> list[ParsedPage]:
        if not isinstance(payload, dict):
            return []
        pdf_info = payload.get("pdf_info")
        if not isinstance(pdf_info, list):
            return []
        pages: list[ParsedPage] = []
        for fallback_index, page in enumerate(pdf_info):
            if not isinstance(page, dict):
                continue
            page_index = page.get("page_idx", page.get("page_no", fallback_index))
            blocks = page.get("preproc_blocks", page.get("para_blocks", []))
            if not isinstance(blocks, list):
                continue
            parsed_blocks: list[ParsedBlock] = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                parsed_blocks.extend(MineruCloudParser._middle_leaf_blocks(block))
            if parsed_blocks:
                pages.append(
                    ParsedPage(
                        number=int(page_index) + 1,
                        text="\n\n".join(block.text for block in parsed_blocks),
                        blocks=parsed_blocks,
                    )
                )
        return pages

    @staticmethod
    def _middle_leaf_blocks(block: dict) -> list[ParsedBlock]:
        nested = block.get("blocks")
        if isinstance(nested, list):
            children = [
                parsed
                for item in nested
                if isinstance(item, dict)
                for parsed in MineruCloudParser._middle_leaf_blocks(item)
            ]
            if children:
                return children
        lines = block.get("lines")
        if isinstance(lines, list):
            line_texts: list[str] = []
            for line in lines:
                if not isinstance(line, dict):
                    continue
                spans = line.get("spans")
                if not isinstance(spans, list):
                    continue
                text = "".join(
                    str(span.get("content", ""))
                    for span in spans
                    if isinstance(span, dict) and span.get("type") in {None, "text"}
                ).strip()
                if text:
                    line_texts.append(text)
            if line_texts:
                bbox = MineruCloudParser._bbox(block.get("bbox"))
                if bbox:
                    return [ParsedBlock(text="\n".join(line_texts), bbox=bbox)]
        text = MineruCloudParser._block_text(block)
        bbox = MineruCloudParser._bbox(block.get("bbox"))
        return [ParsedBlock(text=text, bbox=bbox)] if text and bbox else []

    @staticmethod
    def _content_pages(payload: object) -> list[ParsedPage]:
        if not isinstance(payload, list):
            return []
        grouped_text: dict[int, list[str]] = defaultdict(list)
        grouped_blocks: dict[int, list[ParsedBlock]] = defaultdict(list)
        for item in payload:
            if not isinstance(item, dict):
                continue
            page_index = item.get("page_idx", item.get("page_no", item.get("page", 0)))
            text = MineruCloudParser._block_text(item)
            bbox = MineruCloudParser._bbox(item.get("bbox"))
            number = int(page_index) + 1
            if text:
                grouped_text[number].append(text)
                if bbox:
                    grouped_blocks[number].append(ParsedBlock(text=text, bbox=bbox))
        return [
            ParsedPage(
                number=number,
                text="\n\n".join(parts),
                blocks=grouped_blocks[number],
            )
            for number, parts in sorted(grouped_text.items())
        ]

    @staticmethod
    def _block_text(item: dict) -> str:
        for key in ("text", "table_body", "code_body", "equation"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        list_items = item.get("list_items")
        if isinstance(list_items, list):
            return "\n".join(str(value) for value in list_items if str(value).strip()).strip()
        content = item.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, dict):
            values = [value for value in content.values() if isinstance(value, str)]
            return "\n".join(values).strip()
        return ""

    @staticmethod
    def _bbox(value: object) -> tuple[float, float, float, float] | None:
        if not isinstance(value, list) or len(value) != 4:
            return None
        if not all(isinstance(coordinate, (int, float)) for coordinate in value):
            return None
        coordinates = tuple(float(coordinate) for coordinate in value)
        x0, y0, x1, y1 = coordinates
        if not (0 <= x0 < x1 <= 1000 and 0 <= y0 < y1 <= 1000):
            return None
        return coordinates

    @staticmethod
    def _pages(markdown: str) -> list[ParsedPage]:
        return [ParsedPage(number=1, text=markdown)]
