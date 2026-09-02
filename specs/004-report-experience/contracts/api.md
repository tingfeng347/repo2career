# Report API Contract

- `GET /api/v1/analyses/{id}/artifacts` returns manifest metadata and download URLs.
- `GET /api/v1/analyses/{id}/artifacts/{path}` serves a path validated inside the job report directory.
- The frontend consumes the same job and artifact contracts used by CLI output.

