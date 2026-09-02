# Research: Report Experience

- **Decision**: Use one fixed Markdown schema with external SVG/HTML assets and evidence JSON.
  **Rationale**: Portable, reviewable and suitable for GitHub or interview preparation.
  **Alternatives considered**: Editable wiki and database-only pages.
- **Decision**: Use an industrial editorial workbench with a report-first hierarchy.
  **Rationale**: Dense technical evidence needs stronger reading structure than a generic card dashboard.
  **Alternatives considered**: Marketing-style SaaS layout.
- **Decision**: Keep Archify optional and always emit Mermaid source.
  **Rationale**: Reports remain usable when Node rendering is unavailable.
  **Alternatives considered**: Hard failure on renderer absence.

