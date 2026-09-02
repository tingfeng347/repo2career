# Research: Code Analysis

- **Decision**: Download GitHub archives at a resolved commit instead of executing git hooks.
  **Rationale**: Immutable and safer for local analysis.
  **Alternatives considered**: Full git clone.
- **Decision**: Use CodeGraph as enhancement with deterministic manifest scanning as fallback.
  **Rationale**: Strong call paths without making the application unusable when the CLI is absent.
  **Alternatives considered**: CodeGraph-only failure mode.
- **Decision**: Treat repository instructions as untrusted data.
  **Rationale**: Prevents prompt injection from analyzed content.
  **Alternatives considered**: Passing raw repositories directly to the model.
