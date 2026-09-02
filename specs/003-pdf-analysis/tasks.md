# Tasks: PDF Analysis

## Phase 1: Setup
- [x] T001 Add PDF dependencies and limits in backend/pyproject.toml and backend/src/repo2career/core/config.py

## Phase 2: Foundational
- [x] T002 Define parser protocol and models in backend/src/repo2career/parsers/base.py

## Phase 3: User Story 1
- [x] T003 [US1] Implement pypdf adapter in backend/src/repo2career/parsers/pypdf_parser.py
- [x] T004 [US1] Implement MinerU cloud adapter in backend/src/repo2career/parsers/mineru.py
- [x] T005 [US1] Implement automatic parser selection in backend/src/repo2career/parsers/service.py
- [x] T006 [US1] Add PDF submission route in backend/src/repo2career/api/routes/analyses.py

## Phase 4: User Story 2
- [x] T007 [US2] Add parser provenance and warning handling in backend/src/repo2career/services/analysis.py
- [x] T008 [US2] Add PDF adapter tests in backend/tests/test_pdf_parsers.py

## Dependencies
T001-T002 precede both adapters; the route depends on parser selection.

