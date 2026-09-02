# Data Model: Platform Foundation

## AnalysisJob

- `id`: UUID string
- `source_kind`: github, folder or pdf
- `status`: queued, running, interrupted, completed, failed or cancelled
- `stage`: ingesting, extracting, indexing, analyzing, diagramming, composing or validating
- `progress`: integer 0-100
- `options_json`, `source_json`, `error`, timestamps

Transitions are queued → running → completed/failed/cancelled. A running job becomes interrupted on startup and may return to queued through retry.

## StageEvent

- Monotonic identifier, job identifier, stage, progress, message and timestamp.

## RuntimeSetting

- Key, masked effective value, source (`environment`, `.env`, `default`) and secret flag.
