# Architecture and data-model visuals

These SVGs are editable vector diagrams. They remain sharp when zoomed and can be downloaded directly from GitHub.

| Diagram | Purpose |
|---|---|
| [System architecture](system-architecture.svg) | Scheduled rebuild, validation and PR publication, deployed dashboard, recovery boundary and implemented Gemini AI |
| [Low-level contracts](low-level-contracts.svg) | Transformation rules, key semantics, metric algebra and quality gates |
| [Silver relational model](silver-relational-model.svg) | Eight shared tables, logical keys and optional/multi-valued relationships |
| [Gold star schema](gold-star-schema.svg) | Fact, seven dimensions, role-playing date keys and verified row counts |

## Architecture view set

| File | Editable pages | SVG previews |
|---|---|---|
| `system-architecture.drawio` | HLSD 01 Platform architecture; HLSD 02 Deployment & operations; HLSD 03 AI Analyst | [Platform](system-architecture.svg), [deployment](deployment-operations.svg), [AI Analyst](ai-analyst.svg) |
| `low-level-contracts.drawio` | LLD 01 Source-to-model; LLD 02 Gold-to-dashboard; LLD 03 Release lifecycle | [Processing](low-level-contracts.svg), [serving contracts](serving-contracts.svg), [release lifecycle](release-lifecycle.svg) |

These views follow the [documented design guidance](../../docs/design-guidelines.md), with boundaries, typed components, labeled flows and clear implementation status. Open the draw.io page tabs to access the full design set.

## Visual conventions
Filled icons identify services, files, processing, databases and query structures. Blue marks sources and lookup dimensions; teal marks cleaning, relationships and numerical tooling; gold marks business-ready metrics and the fact; purple marks evidence, date roles or recovery responsibilities. Solid cards represent implemented components; dashed cards represent planned components.

Architecture arrows show data or tool flow. Relational-model arrows show reference relationships, with optional narrative and tag rules called out separately. PK/FK annotations describe dbt-tested logical keys, not enforced DuckDB constraints. Silver and star schema pages retain editable Mermaid definitions; architecture and LLD views are maintained through the draw.io generator.

Architecture and processing contracts were reviewed on 2026-10-07. The first hosted full source download is blocked by HTTP 403; implemented refresh code is not yet operational. Counts describe the verified downloaded snapshot. The dashboard and Gemini chat are implemented; owner model activation was confirmed on 2026-10-07. Permanent full-detail hosting, semantic retrieval and systematic live-quality evaluation remain future work.

## Editable draw.io versions
Open [diagrams.net](https://app.diagrams.net/), choose **File → Open from → Device**, and select one of these downloaded files:

- [System architecture](system-architecture.drawio)
- [Low-level design](low-level-contracts.drawio)
- [Silver model](silver-relational-model.drawio)
- [Gold star schema](gold-star-schema.drawio)

Architecture and LLD files contain grouped component cards with distinct filled vector icons, editable text, boundaries and native connectors. It is not a single flattened screenshot. SVG versions are used for inline GitHub display. The icons are generic engineering symbols, not official vendor logos.

## Regenerate architecture views
Run `python scripts/design/render_architecture.py` from the repository root. The generator produces the architecture and LLD multi-page draw.io files, a standalone AI draw.io file and six matching SVG previews without external image dependencies. Silver and star schema assets remain separate data-model views.

