# Architecture and data-model visuals

These SVGs are editable vector diagrams. They remain sharp when zoomed and can be downloaded directly from GitHub.

| Diagram | Purpose |
|---|---|
| [System architecture](system-architecture.svg) | Scheduled rebuild, validation and PR publication, deployed dashboard, recovery boundary and planned AI |
| [Low-level contracts](low-level-contracts.svg) | Transformation rules, key semantics, metric algebra and quality gates |
| [Silver relational model](silver-relational-model.svg) | Eight shared tables, logical keys and optional/multi-valued relationships |
| [Gold star schema](gold-star-schema.svg) | Fact, seven dimensions, role-playing date keys and verified row counts |

## Architecture view set

| File | Editable pages | SVG previews |
|---|---|---|
| `system-architecture.drawio` | HLSD 01 Platform architecture; HLSD 02 Deployment & operations | [Platform](system-architecture.svg), [deployment](deployment-operations.svg) |
| `low-level-contracts.drawio` | LLD 01 Source-to-model; LLD 02 Gold-to-dashboard; LLD 03 Release lifecycle | [Processing](low-level-contracts.svg), [serving contracts](serving-contracts.svg), [release lifecycle](release-lifecycle.svg) |

These views follow the [documented design guidance](../../docs/design-guidelines.md), with boundaries, typed components, labeled flows and clear implementation status. Open the draw.io page tabs to access the full design set.

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

Architecture and LLD files contain grouped component cards with distinct filled vector icons, editable text, boundaries and native connectors. It is not a single flattened screenshot. SVG versions are used for inline GitHub display. The icons are generic engineering symbols, not official vendor logos.

## Regenerate architecture views
Run `python scripts/design/render_architecture.py` from the repository root. The generator produces the two multi-page draw.io files and five matching SVG previews without external image dependencies. Silver and star schema assets remain separate data-model views.
