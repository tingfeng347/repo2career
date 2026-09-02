# Quickstart Validation: Platform Foundation

1. Copy `.env.example` to `.env` and run `uv sync` in `backend`.
2. Start the API with `uv run repo2career serve`.
3. Open `/api/v1/health` and `/api/v1/capabilities`.
4. Create a fixture analysis, watch its SSE stream, stop the process and restart it.
5. Confirm the active job is interrupted and retryable.
6. Save a test secret and confirm settings only return a mask.
