# Feature Specification: Code Analysis

**Feature Branch**: `002-code-analysis`
**Created**: 2026-09-02
**Status**: Approved
**Input**: Analyze GitHub repositories and uploaded local folders with traceable evidence.

## User Scenarios & Testing

### User Story 1 - Analyze a GitHub repository (Priority: P1)

A user submits a public or private GitHub URL and receives a grounded account of its business flow, technology choices and architecture.

**Why this priority**: Repository understanding is the main product value.
**Independent Test**: Analyze a small public fixture and verify every major finding links to a commit, file and line range.

**Acceptance Scenarios**:
1. **Given** a public repository URL, **When** analysis is started, **Then** its immutable revision is recorded and analyzed.
2. **Given** a private repository and valid token, **When** analysis is started, **Then** content is retrieved without exposing the token.

### User Story 2 - Analyze a local folder (Priority: P2)

A user selects a browser directory and receives the same analysis without exposing unrelated local paths.

**Acceptance Scenarios**:
1. **Given** an uploaded directory, **When** files are accepted, **Then** relative paths are retained and unsafe paths are rejected.

### Edge Cases
- Unsupported or absent CodeGraph must produce a clearly labelled degraded result.
- Symlinks, dependency directories, secrets, binaries and oversized inputs are excluded.
- Instructions contained in target files are evidence, never executable instructions.

## Requirements

### Functional Requirements
- **FR-001**: The system MUST accept GitHub public and private repository sources.
- **FR-002**: The system MUST accept browser directory uploads with preserved relative paths.
- **FR-003**: The system MUST create an immutable, sanitized source snapshot.
- **FR-004**: The system MUST identify entry points, dependencies, routes, data models, integrations and deployment assets.
- **FR-005**: The system MUST trace important runtime and business flows to source evidence.
- **FR-006**: The system MUST continue with a labelled fallback when enhanced analysis is unavailable.
- **FR-007**: The system MUST never execute analyzed project code.

### Key Entities
- **Source Snapshot**: Sanitized files plus origin, revision and exclusions.
- **Code Evidence**: File, line range, revision, excerpt and confidence.
- **Analysis Finding**: A supported statement about business or architecture.

## Success Criteria
- **SC-001**: Every major report claim has at least one navigable source reference.
- **SC-002**: A 5,000-file repository is accepted without blocking other interface actions.
- **SC-003**: No excluded secret file or credential appears in generated evidence.
- **SC-004**: Missing enhanced tooling does not prevent completion for supported text repositories.

## Assumptions
- Git history beyond the selected revision is outside version-one scope.
- The default limits are 20,000 files and 1 GB per project.
