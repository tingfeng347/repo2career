# Implementation Plan: Code Analysis

**Branch**: `002-code-analysis` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Stream GitHub archives or browser folder files into a sanitized workspace, collect deterministic metadata, enrich it through CodeGraph and synthesize evidence-backed findings with DeepSeek.

## Technical Context
**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI UploadFile, httpx, AsyncOpenAI, CodeGraph CLI
**Storage**: Per-job filesystem snapshots and JSON evidence
**Testing**: pytest, mocked HTTP and subprocess adapters
**Target Platform**: Linux, macOS and Windows
**Project Type**: Backend service and CLI
**Performance Goals**: Non-blocking ingestion and bounded evidence payloads
**Constraints**: No target code execution; strict path and size guards
**Scale/Scope**: 20,000 files or 1 GB per source

## Constitution Check
Constitution template skipped; approved security and simplicity constraints pass.

## Project Structure
```text
backend/src/repo2career/
├── analyzers/
├── inputs/
├── services/analysis.py
└── api/routes/analyses.py
backend/tests/test_code_analysis.py
```

**Structure Decision**: Input, evidence collection and model synthesis are independent adapters behind one pipeline.

## Complexity Tracking
No violations.
