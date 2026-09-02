from __future__ import annotations

import asyncio
from pathlib import Path

from pypdf import PdfReader

from repo2career.parsers.base import ParsedDocument, ParsedPage, PdfParserKind


class PypdfParser:
    async def parse(self, path: Path, password: str | None = None) -> ParsedDocument:
        return await asyncio.to_thread(self._parse_sync, path, password)

    @staticmethod
    def _parse_sync(path: Path, password: str | None) -> ParsedDocument:
        reader = PdfReader(path, strict=False)
        if reader.is_encrypted:
            if not password or reader.decrypt(password) == 0:
                raise ValueError("PDF is encrypted and the password is missing or incorrect")
        metadata = {
            str(key).lstrip("/"): str(value) for key, value in (reader.metadata or {}).items()
        }
        pages: list[ParsedPage] = []
        markdown_parts = []
        warnings = ["pypdf does not perform OCR; image-only pages may be empty."]
        for number, page in enumerate(reader.pages, start=1):
            try:
                text = (page.extract_text() or "").strip()
                warning = (
                    None if text else "No text extracted; this page may be scanned or image-only."
                )
            except Exception as exc:  # malformed page objects vary by producer
                text = ""
                warning = f"Page extraction failed: {type(exc).__name__}"
            pages.append(ParsedPage(number=number, text=text, warning=warning))
            markdown_parts.append(f"## Page {number}\n\n{text or '*No extractable text*'}")
            if warning:
                warnings.append(f"Page {number}: {warning}")
        if not pages:
            raise ValueError("PDF contains no pages")
        return ParsedDocument(
            filename=path.name,
            parser=PdfParserKind.PYPDF,
            metadata=metadata,
            pages=pages,
            markdown="\n\n".join(markdown_parts),
            warnings=warnings,
        )
