# Tasks: Platform Foundation

## Phase 1: Setup
- [x] T001 Create backend uv package and environment templates in backend/pyproject.toml and .env.example
- [x] T002 Create React workspace configuration in frontend/package.json and frontend/vite.config.ts

## Phase 2: Foundational
- [x] T003 Implement settings and shared models in backend/src/repo2career/core/config.py and backend/src/repo2career/models/domain.py
- [x] T004 Implement SQLite job repository in backend/src/repo2career/db/jobs.py

## Phase 3: User Story 1
- [x] T005 [US1] Implement asynchronous job manager in backend/src/repo2career/services/jobs.py
- [x] T006 [US1] Implement lifecycle and SSE routes in backend/src/repo2career/api/routes/jobs.py
- [x] T007 [US1] Add lifecycle tests in backend/tests/test_jobs.py

## Phase 4: User Story 2
- [x] T008 [US2] Implement masked settings service in backend/src/repo2career/core/config.py
- [x] T009 [US2] Implement settings and capability routes in backend/src/repo2career/api/routes/settings.py
- [x] T010 [US2] Add settings security tests in backend/tests/test_settings.py

## Phase 5: Polish
- [x] T011 Create CLI and application entry points in backend/src/repo2career/cli.py and backend/src/repo2career/main.py

## Dependencies
T001-T004 precede story tasks. US1 and US2 may then proceed independently.

## Implementation Strategy
Complete the durable job lifecycle first, then add settings and adapters.

