# Research: PDF Analysis

- **Decision**: MinerU uses the official v4 presigned upload and batch-result endpoints.
  **Rationale**: Supports asynchronous progress and high-quality structured extraction.
  **Alternatives considered**: Local GPU deployment.
- **Decision**: pypdf is the only automatic fallback and runs locally in a worker thread.
  **Rationale**: Lightweight and private, with honest OCR limitations.
  **Alternatives considered**: Automatic OCR installation.
