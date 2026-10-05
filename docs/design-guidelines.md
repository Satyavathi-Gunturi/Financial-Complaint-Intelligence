# Architecture documentation and diagram conventions

Reviewed 2026-10-05. This project adapts published architecture guidance to its actual data engineering implementation. HLSD and LLD are document/view names used here; the guidance below is not a claim of certification or compliance with a universal HLSD/LLD template.

## Authoritative guidance

| Reference | Guidance adopted | Application in this repository |
|---|---|---|
| [C4 notation](https://c4model.com/diagrams/notation) | Title and scope; explicit element types, responsibilities and technologies; labeled directional relationships; legend | Every architecture page identifies scope, component role, technology and flow meaning |
| [C4 container view](https://c4model.com/diagrams/container) | Describe applications and data stores and their responsibilities | HLSD platform architecture separates source, processing, release and consumption |
| [C4 deployment view](https://c4model.com/diagrams/deployment) | Show execution environments and deployed instances; explain icon notation | HLSD deployment page identifies temporary runner, repository, Streamlit and development recovery |
| [C4 component view](https://c4model.com/diagrams/component) | Decompose implementation responsibilities and technology details | LLD processing page details Python ingestion and dbt layers; it is an adapted pipeline contract view, not a strict single-container C4 diagram |
| [Microsoft medallion data warehouse guidance](https://learn.microsoft.com/en-us/azure/architecture/databases/architecture/dataops-mdw) | Distinguish raw, refined and analytical responsibilities; record lineage; gate publication on data tests; address reliability, security and operations | LLD documents schema boundaries, provenance, grain, metrics, reconciliation and failure contracts; HLSD records operational trade-offs |
| [arc42 overview](https://arc42.org/overview) | Separate context, building blocks, runtime, deployment, quality requirements, decisions and risks | Documents contain view catalogues, requirements, deployment, release runtime, decisions and open operational risks |

C4 is notation-independent. Filled icons, navy headers and layer colors are this project's visual convention, not a prescribed industry standard. Microsoft guidance is used for design principles; the implementation remains DuckDB/dbt/GitHub/Streamlit, with no implied Microsoft Fabric or AWS deployment.

## View hierarchy

| Level | Include | Keep in another view |
|---|---|---|
| Architecture / HLSD | System boundaries, external ownership, container responsibilities, deployment environments, lifecycle, quality requirements and decisions | Detailed field lists and transformation algorithms belong in LLD |
| LLD | Named schemas/components, grain and identity, retention rules, interface contracts, algorithms, failure states and validation gates | Table-level relationships and exact schema columns belong in ER diagrams and versioned SQL/YAML |
| ER and star views | Logical keys, cardinality, fact grain and date roles | Source scheduling and deployment boundaries belong in HLSD |

## Project-specific departures and limitations

- The scheduled `bronze_complaints` table is retention-filtered and deduplicated. It is a working bronze input, not the immutable all-history raw layer described in an enterprise medallion reference. ZIP caching is disposable and durable source-byte version storage is not implemented.
- Category keys are deterministic MD5 hashes over JSON labels. They are not a corporate master-data service or an identity-generated warehouse key mapping.
- Wide gold and star are parallel query representations with shared metric calculation; no independent benchmark or agent evaluation has run.
- Publication validation and a release commit establish a repository revision. They do not establish a measured Streamlit deployment completion time or a freshness SLA.
- The first hosted archive download returned HTTP 403. A successful full real-source rolling release remains an acceptance requirement; the historical dashboard stays current until that succeeds.

## Visual and review rules

Each page has a bounded purpose, readable hierarchy, generous spacing and a legend. Source/lookup elements use blue; processing uses teal; analytical data uses gold; metadata/recovery/planned AI uses purple; failure callouts use red. Component types also have distinct filled symbols and textual types, so meaning does not rely on color alone. Solid and dashed relationships distinguish data/publication flow from control/development flow. Planned components are explicitly labeled and dashed.

The draw.io files contain native boundaries, cards, text and routed connectors. Each component groups its title, descriptions and embedded vector icon so it can be moved together. Icons are self-contained generic symbols, not vendor logos or a flattened page screenshot. Matching SVGs provide sharp repository previews.

Rebuild the views from the repository root:

```bash
python scripts/design/render_architecture.py
```

Review changes against maintained source code; open both draw.io files and inspect every page. Rendering QA checks text clipping, overlaps, arrow routing, boundaries, legends, current status and implemented/planned distinctions. The generator does not infer architecture from code: design changes require updating its component definitions and the accompanying documents.
