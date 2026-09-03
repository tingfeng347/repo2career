import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest
from pypdf import PdfWriter

from repo2career.core.config import Settings
from repo2career.parsers.base import ParsedDocument, ParsedPage, PdfParserKind
from repo2career.parsers.mineru import MineruCloudParser
from repo2career.parsers.pypdf_parser import PypdfParser
from repo2career.parsers.service import PdfParserService
from repo2career.services.analysis import AnalysisService


@pytest.mark.asyncio
async def test_pypdf_reports_blank_pages(tmp_path: Path) -> None:
    path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as output:
        writer.write(output)
    document = await PypdfParser().parse(path)
    assert document.parser == PdfParserKind.PYPDF
    assert document.pages[0].warning
    assert any("OCR" in warning for warning in document.warnings)


def test_auto_parser_uses_key_presence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "")
    assert PdfParserService(Settings.load()).selected() == PdfParserKind.PYPDF
    monkeypatch.setenv("MINERU_API_KEY", "token")
    assert PdfParserService(Settings.load()).selected() == PdfParserKind.MINERU


@pytest.mark.asyncio
async def test_mineru_failure_falls_back_to_pypdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "fallback.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as output:
        writer.write(output)

    async def fail(*args, **kwargs):
        raise RuntimeError("401 Unauthorized")

    monkeypatch.setattr(MineruCloudParser, "parse", fail)
    monkeypatch.setenv("MINERU_API_KEY", "configured")
    document = await PdfParserService(Settings.load()).parse(path, PdfParserKind.AUTO)
    assert document.parser == PdfParserKind.PYPDF
    assert "已回退到 pypdf" in document.warnings[0]


def test_mineru_archive_preserves_page_evidence() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("document/full.md", "# Example\n\nFirst page\n\nSecond page")
        archive.writestr(
            "document/content_list.json",
            json.dumps(
                [
                    {"page_idx": 0, "text": "First page", "bbox": [100, 100, 900, 200]},
                    {"page_idx": 1, "text": "Second page"},
                ]
            ),
        )
    markdown, pages = MineruCloudParser._read_result(buffer.getvalue(), "result.zip")
    assert markdown.startswith("# Example")
    assert [(page.number, page.text) for page in pages] == [
        (1, "First page"),
        (2, "Second page"),
    ]
    assert pages[0].blocks[0].bbox == (100.0, 100.0, 900.0, 200.0)
    evidence = AnalysisService._pdf_evidence(
        ParsedDocument(filename="result.pdf", parser=PdfParserKind.MINERU, pages=pages)
    )
    assert evidence.references[0].id == "pdf-page-1-block-1"
    assert evidence.references[0].bbox == (100.0, 100.0, 900.0, 200.0)


def test_mineru_archive_prefers_precise_middle_json_blocks() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("document/full.md", "Precise paragraph")
        archive.writestr(
            "document/content_list.json",
            json.dumps(
                [{"page_idx": 0, "text": "Precise paragraph", "bbox": [0, 0, 1000, 1000]}]
            ),
        )
        archive.writestr(
            "document/full_middle.json",
            json.dumps(
                {
                    "pdf_info": [
                        {
                            "page_idx": 0,
                            "preproc_blocks": [
                                {
                                    "bbox": [80, 180, 900, 500],
                                    "type": "list",
                                    "blocks": [{
                                        "bbox": [120, 240, 760, 310],
                                        "lines": [
                                        {
                                            "bbox": [120, 240, 760, 270],
                                            "spans": [
                                                {"type": "text", "content": "Precise "},
                                                {"type": "text", "content": "paragraph"},
                                            ],
                                        }
                                        ],
                                    }],
                                }
                            ],
                        }
                    ]
                }
            ),
        )

    _, pages = MineruCloudParser._read_result(buffer.getvalue(), "result.zip")

    assert pages[0].text == "Precise paragraph"
    assert pages[0].blocks[0].bbox == (120.0, 240.0, 760.0, 310.0)


def test_mineru_401_explains_token_type() -> None:
    response = httpx.Response(401, request=httpx.Request("POST", "https://mineru.net/api/v4/file-urls/batch"))
    with pytest.raises(RuntimeError, match="不要使用网页登录 JWT"):
        MineruCloudParser._payload(response)


def test_pdf_evidence_is_split_into_page_addressable_parts() -> None:
    document = ParsedDocument(
        filename="project.pdf",
        parser=PdfParserKind.PYPDF,
        pages=[ParsedPage(number=2, text="First fact.\n\nSecond fact.")],
    )

    evidence = AnalysisService._pdf_evidence(document)

    assert evidence.references[0].id == "pdf-page-2-part-1"
    assert evidence.references[0].page == 2
