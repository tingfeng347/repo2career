from __future__ import annotations

from pathlib import Path

from repo2career.core.config import Settings
from repo2career.parsers.base import ParsedDocument, PdfParserKind
from repo2career.parsers.mineru import MineruCloudParser
from repo2career.parsers.pypdf_parser import PypdfParser


class PdfParserService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def selected(self, requested: PdfParserKind = PdfParserKind.AUTO) -> PdfParserKind:
        if requested != PdfParserKind.AUTO:
            return requested
        return PdfParserKind.MINERU if self.settings.mineru_api_key else PdfParserKind.PYPDF

    async def parse(
        self, path: Path, requested: PdfParserKind, password: str | None = None
    ) -> ParsedDocument:
        selected = self.selected(requested)
        if selected == PdfParserKind.MINERU:
            try:
                return await MineruCloudParser(self.settings).parse(path, password)
            except Exception as exc:
                # Cloud credentials and endpoints can expire independently of the local app.
                # Keep the analysis usable and make the fallback explicit in the report evidence.
                document = await PypdfParser().parse(path, password)
                detail = str(exc).splitlines()[0][:180]
                document.warnings.insert(
                    0, f"MinerU 不可用（{type(exc).__name__}: {detail}），已回退到 pypdf。"
                )
                return document
        return await PypdfParser().parse(path, password)
