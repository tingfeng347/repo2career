# Research: Platform Foundation

- **Decision**: Use an in-process asynchronous worker with a SQLite WAL job store.
  **Rationale**: Durable enough for one local user without Redis or a second service.
  **Alternatives considered**: Redis workers and ephemeral background tasks.
- **Decision**: Use SSE for progress.
  **Rationale**: One-way ordered updates are sufficient and simpler than WebSockets.
  **Alternatives considered**: Polling and WebSockets.
- **Decision**: Apply blocking filesystem and parser work through thread or subprocess boundaries.
  **Rationale**: Keeps the application event loop responsive.
  **Alternatives considered**: Synchronous request handlers.
