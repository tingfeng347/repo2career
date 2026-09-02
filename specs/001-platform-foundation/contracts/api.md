# Platform API Contract

- `GET /api/v1/health` returns service health.
- `GET /api/v1/capabilities` returns CodeGraph, Archify, DeepSeek and PDF parser availability.
- `GET /api/v1/analyses/{id}` returns the durable job view.
- `GET /api/v1/analyses/{id}/events` emits SSE progress events.
- `POST /api/v1/analyses/{id}/cancel` cancels an active job.
- `POST /api/v1/analyses/{id}/retry` queues a failed or interrupted job.
- `GET /api/v1/settings` returns masked effective settings.
- `PUT /api/v1/settings` accepts only documented keys.
- `POST /api/v1/settings/test-deepseek` checks model connectivity.
- `POST /api/v1/settings/test-mineru` checks whether MinerU credentials are configured.
