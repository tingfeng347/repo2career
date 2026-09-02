# Implementation Plan: Platform Foundation

**Branch**: `001-platform-foundation` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Build a local-first asynchronous job platform shared by FastAPI, Typer and a React workbench. Persist state in SQLite, stream progress with SSE and load allowlisted configuration from environment variables and `.env`.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript 5
**Primary Dependencies**: FastAPI, Pydantic, aiosqlite, python-dotenv, Typer, React, TanStack Query
**Storage**: SQLite WAL and per-job filesystem artifacts
**Testing**: pytest, pytest-asyncio, Vitest, React Testing Library
**Target Platform**: Linux, macOS and Windows local application
**Project Type**: Web application plus CLI
**Performance Goals**: Job acknowledgement and progress visibility under two seconds
**Constraints**: Single user, one worker, no secret responses, non-blocking event loop
**Scale/Scope**: Thousands of retained local jobs

## Constitution Check

The constitution is an unfilled template and is therefore skipped. The plan follows the approved scope and avoids optional infrastructure.

## Project Structure

```text
backend/src/repo2career/
├── api/
├── core/
├── db/
├── models/
└── services/
backend/tests/
frontend/src/
├── components/
├── pages/
└── services/
```

**Structure Decision**: A Python backend package owns domain behavior; the React app and Typer CLI are thin adapters.

## Complexity Tracking

No constitution violations or exceptional complexity.
