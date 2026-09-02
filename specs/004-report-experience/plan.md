# Implementation Plan: Report Experience

**Branch**: `004-report-experience` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary
Validate structured findings, render a fixed Markdown report and diagram bundle, and expose the same workflow through a deliberately designed React workbench and Typer CLI.

## Technical Context
**Language/Version**: Python 3.12+, TypeScript 5
**Primary Dependencies**: Pydantic, Markdown rendering, Archify adapter, React, shadcn-style primitives
**Storage**: Job report directory
**Testing**: pytest report golden tests, Vitest and Playwright-ready UI
**Target Platform**: Linux, macOS and Windows desktop browser and terminal
**Project Type**: Web application plus CLI
**Performance Goals**: Report navigation responds immediately after job completion
**Constraints**: Fixed section schema, evidence-first, responsive layout
**Scale/Scope**: One report bundle per job

## Constitution Check
Constitution template skipped; evidence and simplicity gates pass.

## Project Structure
```text
backend/src/repo2career/reports/
frontend/src/
├── components/
├── pages/
├── services/
└── styles/
```

**Structure Decision**: The backend owns report truth and artifact generation; the frontend renders API state only.

## Complexity Tracking
No violations.
