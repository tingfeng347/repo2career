# Tasks: Report Experience

## Phase 1: Setup
- [x] T001 Add report and frontend build configuration in backend/src/repo2career/reports and frontend/src

## Phase 2: Foundational
- [x] T002 Implement fixed report schema in backend/src/repo2career/reports/schema.py
- [x] T003 Implement Markdown and diagram rendering in backend/src/repo2career/reports/render.py

## Phase 3: User Story 1
- [x] T004 [US1] Implement artifact API in backend/src/repo2career/api/routes/artifacts.py
- [x] T005 [US1] Implement source selection and job progress UI in frontend/src/App.tsx
- [x] T006 [US1] Implement report and evidence workbench in frontend/src/components/ReportWorkbench.tsx

## Phase 4: User Story 2
- [x] T007 [US2] Add job-search report sections in backend/src/repo2career/reports/render.py
- [x] T008 [US2] Add report schema tests in backend/tests/test_reports.py

## Phase 5: User Story 3
- [x] T009 [US3] Add analysis, jobs, report, config, doctor and serve CLI commands in backend/src/repo2career/cli.py

## Phase 6: Polish
- [x] T010 Add responsive styling and frontend tests in frontend/src/styles.css and frontend/src/App.test.tsx
- [x] T011 Document setup and operation in README.md

## Dependencies
T001-T003 precede all user stories. US1 and US3 consume the same APIs; US2 extends report content.


