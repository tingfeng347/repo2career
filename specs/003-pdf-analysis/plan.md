# Implementation Plan: PDF Analysis

**Branch**: `003-pdf-analysis` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary
Implement one parser protocol with MinerU cloud and pypdf adapters, automatic selection by effective configuration and page-grounded normalized output.

## Technical Context
**Language/Version**: Python 3.12+
**Primary Dependencies**: httpx, pypdf[crypto], MinerU v4 API
**Storage**: Job input and normalized JSON/Markdown artifacts
**Testing**: pytest with HTTP fixtures and generated PDFs
**Target Platform**: Linux, macOS and Windows
**Project Type**: Backend service and CLI
**Performance Goals**: Non-blocking parsing with visible progress
**Constraints**: 200 MB default limit, no silent cloud fallback, no password persistence
**Scale/Scope**: One PDF per job

## Constitution Check
Constitution template skipped; privacy and simplicity gates pass.

## Project Structure
```text
backend/src/repo2career/parsers/
├── base.py
├── mineru.py
└── pypdf_parser.py
backend/tests/test_pdf_parsers.py
```

**Structure Decision**: Both adapters return the same parsed-document model.
