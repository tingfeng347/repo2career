# Feature Specification: Platform Foundation

**Feature Branch**: `001-platform-foundation`
**Created**: 2026-09-02
**Status**: Approved
**Input**: Local-first analysis platform shared by web and command-line users.

## User Scenarios & Testing

### User Story 1 - Start and monitor an analysis (Priority: P1)

A local user can create a durable analysis job and follow its current stage without blocking the interface.

**Why this priority**: Every source type depends on a reliable job lifecycle.
**Independent Test**: Create a sample job, observe queued and running states, then verify completion is retained after restart.

**Acceptance Scenarios**:

1. **Given** a valid request, **When** the user starts analysis, **Then** a job identifier is returned immediately.
2. **Given** a running job, **When** progress changes, **Then** the user receives ordered stage updates.
3. **Given** an interrupted process, **When** the app restarts, **Then** the job is marked interrupted and can be retried.

### User Story 2 - Configure local integrations (Priority: P2)

A user can configure model and parser credentials locally and verify them without exposing secrets.

**Acceptance Scenarios**:

1. **Given** a saved credential, **When** settings are viewed, **Then** only a masked value and its source are shown.
2. **Given** valid model settings, **When** connectivity is tested, **Then** the user receives a clear success result.

### Edge Cases

- A duplicate retry must not create conflicting job state.
- Cancellation during an external operation must leave the job in a terminal state.
- A system environment variable must take precedence over the local configuration file.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST create durable jobs with unique identifiers and ordered lifecycle states.
- **FR-002**: The system MUST stream progress and retain completed stage metadata.
- **FR-003**: Users MUST be able to cancel failed or running jobs and retry interrupted or failed jobs.
- **FR-004**: The web interface and command-line interface MUST use the same analysis behavior.
- **FR-005**: Users MUST be able to update an allowlisted set of local settings.
- **FR-006**: The system MUST never return stored secret values through its settings interface.
- **FR-007**: The system MUST report integration capabilities and actionable setup failures.

### Key Entities

- **Analysis Job**: A durable request with source, language, status, stage, progress and error data.
- **Stage Event**: An ordered progress update associated with a job.
- **Runtime Setting**: An effective value, source and sensitivity classification.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A job identifier is visible within two seconds of submission.
- **SC-002**: At least 95% of stage transitions appear to the user within two seconds.
- **SC-003**: All jobs that were active during shutdown are recoverable as interrupted jobs after restart.
- **SC-004**: No secret plaintext appears in settings responses, job records or application logs.

## Assumptions

- Version one is local and single-user.
- One analysis runs at a time by default.
- Authentication, remote workers and cloud storage are outside scope.
