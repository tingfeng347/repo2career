# Feature Specification: PDF Analysis

**Feature Branch**: `003-pdf-analysis`
**Created**: 2026-09-02
**Status**: Approved
**Input**: Parse project PDFs with MinerU when configured and pypdf otherwise.

## User Scenarios & Testing

### User Story 1 - Parse with automatic selection (Priority: P1)
A user uploads a PDF and receives page-grounded project analysis without having to choose a parser.

**Independent Test**: Run once with a MinerU key and once without it; verify parser provenance and page references.

**Acceptance Scenarios**:
1. **Given** a configured MinerU key, **When** a PDF is uploaded, **Then** cloud parsing is selected and disclosed.
2. **Given** no MinerU key, **When** a PDF is uploaded, **Then** local pypdf parsing is selected automatically.

### User Story 2 - Understand parsing limitations (Priority: P2)
A user sees which pages could not be extracted and can choose a different parser after a failure.

**Acceptance Scenarios**:
1. **Given** an image-only PDF under pypdf, **When** parsing completes, **Then** empty pages and lack of OCR are reported.
2. **Given** a configured but failing MinerU request, **When** parsing fails, **Then** the job does not silently change parser.

### Edge Cases
- Encrypted, corrupt, oversized and zero-page PDFs return actionable errors.
- Temporary PDF passwords are never persisted.

## Requirements
- **FR-001**: The system MUST choose MinerU when its key is configured and pypdf otherwise.
- **FR-002**: Users MUST be able to explicitly select either available parser.
- **FR-003**: The result MUST identify parser provenance and preserve page-level evidence.
- **FR-004**: MinerU uploads and status polling MUST expose progress and bounded timeout failures.
- **FR-005**: pypdf extraction MUST report empty or likely scanned pages.
- **FR-006**: Configured MinerU failures MUST require an explicit retry or parser change.
- **FR-007**: The system MUST reject PDFs over the configured limit.

### Key Entities
- **Parsed Document**: Metadata, page text, Markdown, warnings and parser provenance.
- **Parsed Page**: Page number, text and extraction warning.

## Success Criteria
- **SC-001**: Parser selection is visible before and after every PDF job.
- **SC-002**: Every extracted PDF claim can reference at least one page.
- **SC-003**: No PDF or password leaves the machine in pypdf mode.
- **SC-004**: All blank pages are represented in parser warnings.

## Assumptions
- MinerU is a third-party cloud service and requires explicit disclosure.
- pypdf does not provide OCR.
