# Code Analysis API Contract

- `POST /api/v1/analyses/github` accepts `repository_url`, optional `ref`, language and model.
- `POST /api/v1/analyses/folder` accepts multipart files with relative paths plus language and model.
- Both return HTTP 202 with a durable job identifier.
- Invalid paths, limits or repository URLs return a structured 4xx error before a job runs.
