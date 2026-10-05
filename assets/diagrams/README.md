# Architecture and data-model visuals

These SVGs are editable vector diagrams. They remain sharp when zoomed and can be downloaded directly from GitHub.

| Diagram | Purpose |
|---|---|
| [System architecture](system-architecture.svg) | Scheduled rebuild, validation and PR publication, deployed dashboard, recovery boundary and planned AI |
| [Low-level contracts](low-level-contracts.svg) | Transformation rules, key semantics, metric algebra and quality gates |
| [Silver relational model](silver-relational-model.svg) | Eight shared tables, logical keys and optional/multi-valued relationships |
| [Gold star schema](gold-star-schema.svg) | Fact, seven dimensions, role-playing date keys and verified row counts |

## Visual conventions
Filled icons identify services, files, processing, databases and query structures. Blue marks sources and lookup dimensions; teal marks cleaning, relationships and numerical tooling; gold marks business-ready metrics and the fact; purple marks evidence, date roles or recovery responsibilities. Solid cards represent implemented components; dashed cards represent planned components.

Architecture arrows show data or tool flow. Relational-model arrows show reference relationships, with optional narrative and tag rules called out separately. PK/FK annotations describe dbt-tested logical keys, not enforced DuckDB constraints. Full editable Mermaid definitions remain in the corresponding documentation pages as secondary representations.

Architecture and processing contracts were updated on 2026-10-05. The first hosted full source download is blocked by HTTP 403; implemented refresh code is not yet operational. Counts describe the verified downloaded snapshot. Future hosting and AI components are explicitly planned.

## Editable draw.io versions
Open [diagrams.net](https://app.diagrams.net/), choose **File → Open from → Device**, and select one of these downloaded files:

- [System architecture](system-architecture.drawio)
- [Low-level design](low-level-contracts.drawio)
- [Silver model](silver-relational-model.drawio)
- [Gold star schema](gold-star-schema.drawio)

Each file contains grouped icon nodes, editable text, containers and native connectors. It is not a single flattened screenshot. SVG versions are used for inline GitHub display. The icons are generic engineering symbols, not official vendor logos.
