# Tasks: Code Analysis

## Phase 1: Setup
- [x] T001 Define input limits and exclusions in backend/src/repo2career/core/config.py

## Phase 2: Foundational
- [x] T002 Implement safe workspace utilities in backend/src/repo2career/inputs/workspace.py
- [x] T003 Implement evidence models in backend/src/repo2career/models/evidence.py

## Phase 3: User Story 1
- [x] T004 [US1] Implement GitHub archive ingestion in backend/src/repo2career/inputs/github.py
- [x] T005 [US1] Implement deterministic scanner in backend/src/repo2career/analyzers/scanner.py
- [x] T006 [US1] Implement CodeGraph adapter in backend/src/repo2career/analyzers/codegraph.py
- [x] T007 [US1] Implement DeepSeek synthesis in backend/src/repo2career/analyzers/deepseek.py

## Phase 4: User Story 2
- [x] T008 [US2] Implement folder upload ingestion in backend/src/repo2career/api/routes/analyses.py
- [x] T009 [US2] Add code input security and fallback tests in backend/tests/test_workspace.py

## Phase 5: Polish
- [x] T010 Wire the code pipeline into backend/src/repo2career/services/analysis.py

## Dependencies
T001-T003 precede both stories. US2 reuses the scanner and synthesis pipeline from US1.

