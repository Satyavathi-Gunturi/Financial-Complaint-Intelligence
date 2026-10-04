# Architecture and data-model visuals

These SVGs are editable vector diagrams. They remain sharp when zoomed and can be downloaded directly from GitHub.

| Diagram | Purpose |
|---|---|
| [System architecture](system-architecture.svg) | Implemented data plane, checkpoint boundary and planned executive application |
| [Low-level contracts](low-level-contracts.svg) | Transformation rules, key semantics, metric algebra and quality gates |
| [Silver relational model](silver-relational-model.svg) | Eight shared tables, logical keys and optional/multi-valued relationships |
| [Gold star schema](gold-star-schema.svg) | Fact, seven dimensions, role-playing date keys and verified row counts |

## Visual conventions
Navy headers identify the scope. Blue marks sources and lookup dimensions; teal marks cleaning, relationships and numerical tooling; gold marks business-ready metrics and the fact; purple marks evidence, date roles or recovery responsibilities. Solid cards represent implemented components; dashed cards represent planned components.

Architecture arrows show data or tool flow. Relational-model arrows show reference relationships, with optional narrative and tag rules called out separately. PK/FK annotations describe dbt-tested logical keys, not enforced DuckDB constraints. Full editable Mermaid definitions remain in the corresponding documentation pages as secondary representations.

The design baseline is 2026-10-04. Counts describe the verified downloaded snapshot. Future hosting and AI components are explicitly planned.
