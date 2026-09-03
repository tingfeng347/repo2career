# Feature Specification: Report Experience

**Feature Branch**: `004-report-experience`
**Created**: 2026-09-02
**Status**: Approved
**Input**: Produce a fixed evidence-backed report for technical interviews and job applications.

## User Scenarios & Testing

### User Story 1 - Read and download a complete report (Priority: P1)
A user can navigate a consistent report, inspect evidence beside claims and download its artifact bundle.

**Independent Test**: Complete a fixture analysis and verify all required sections, diagrams and evidence links.

**Acceptance Scenarios**:
1. **Given** completed analysis, **When** the report opens, **Then** its sections, diagrams and parser/tool provenance are visible.
2. **Given** a supported claim, **When** its evidence is selected, **Then** the relevant code range or PDF page is shown.
3. **Given** a PDF or Markdown source, **When** a report citation is selected, **Then** the matching source block is brought into view and highlighted with the citation color.

### User Story 2 - Turn evidence into interview material (Priority: P2)
A user receives resume bullets, a STAR narrative and interview questions grounded in the same project evidence.

**Acceptance Scenarios**:
1. **Given** insufficient evidence for a metric, **When** job-search content is generated, **Then** no fabricated metric is introduced.
2. **Given** a language choice, **When** the report is generated, **Then** all narrative sections use that language.

### User Story 3 - Use the same flow from CLI (Priority: P3)
A terminal user can submit sources, monitor jobs and locate reports without the web interface.

**Acceptance Scenarios**:
1. **Given** a source path or URL, **When** the CLI command runs, **Then** it uses the same pipeline and returns the artifact path.

### Edge Cases
- Missing diagram tooling produces portable Mermaid rather than an empty section.
- Unsupported claims are listed under evidence gaps instead of omitted silently.

## Requirements
- **FR-001**: Every report MUST use the fixed approved section order.
- **FR-002**: Every major claim MUST link to evidence or be labelled as inference or evidence gap.
- **FR-003**: Reports MUST include business flow, technical selection and architecture diagrams when evidence supports them.
- **FR-004**: Reports MUST include resume bullets, STAR narrative and interview questions without inventing metrics.
- **FR-005**: Users MUST be able to choose simplified Chinese or English, with Chinese as default.
- **FR-006**: Users MUST be able to download Markdown, diagrams, evidence and a manifest as one report bundle.
- **FR-007**: Web and CLI output MUST have the same content structure.
- **FR-008**: PDF evidence MUST retain MinerU page and normalized bounding-box coordinates when available.
- **FR-009**: Markdown evidence MUST retain its source line range.
- **FR-010**: The WebUI MUST use a stable color per evidence identifier on both source and report panes.
- **FR-011**: PDF highlighting MUST fall back to text matching, then page-level highlighting when block coordinates are unavailable.

### Key Entities
- **Report Manifest**: Source, tool provenance, language, model, artifacts and warnings.
- **Report Section**: Stable identifier, title and rendered content.
- **Diagram**: Kind, source representation and exported asset paths.

## Success Criteria
- **SC-001**: One hundred percent of completed reports contain all mandatory sections.
- **SC-002**: One hundred percent of major factual claims are evidence-linked or explicitly qualified.
- **SC-003**: Users can reach any report section or its evidence in at most two interactions.
- **SC-004**: CLI and web runs over the same fixture pass the same report structure validator.
- **SC-005**: A PDF or Markdown citation reaches its highlighted source location in one interaction.

## Assumptions
- Reports are read-only in version one.
- PDF export and collaborative editing are outside scope.
