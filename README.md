# Financial Complaint Intelligence

An AI engineering project in progress: a tested CFPB complaint data platform for leadership analytics and a planned evidence-backed data agent.

## Problem statement
Financial-services leadership needs a reliable way to identify changing complaint patterns and investigate the customer experiences behind them. This project prepares consistent complaint metrics and narrative evidence for a dashboard and a data agent that can answer questions using SQL calculations and cited complaint records.

The intended decisions are which complaint categories need investigation, where volumes are changing, and how recorded response outcomes differ. Public complaints cannot establish internal root causes, customer satisfaction, company-wide incident rates or financial losses.

## Current verified scope
| Measure | Result |
|---|---:|
| Selected archive exports | 18 |
| Unique complaints | 14,482,997 |
| Published narratives | 2,711,935 |
| Observed received dates | 2022-11-01 to 2026-08-31 |
| Bronze Parquet files | 299 |
| Bronze Parquet size | Approximately 733 MB |
| Silver tables | 8 |
| Additional star schema | 1 fact table and 7 dimensions |

## Implemented and planned
**Implemented in Colab:** chunked CSV ingestion, bronze Parquet with provenance, profiling, dbt staging and silver, complaint-level wide gold with metric flags, an additional gold star schema, reconciliation tests and Drive checkpoints. The saved notebook includes successful builds; [validation results](docs/data-quality-results.md) record their observed counts.

**Planned:** permanent data hosting, dashboard, read-only SQL agent, semantic narrative retrieval, LLM integration, evaluation of both query structures, application deployment and production monitoring. There is no live AI app yet.

## Architecture
This project combines **medallion architecture** with **two gold query structures**. Silver is shared; wide gold remains available alongside the additional star schema. The star models reuse the existing gold metric definitions rather than replacing them.

```mermaid
flowchart TD
    A[CFPB archive ZIPs] --> B[Bronze Parquet]
    B --> C[dbt staging]
    C --> D[Normalized silver]
    D --> E[Wide gold metrics]
    E --> F[Gold star schema]
    E --> G[Planned dashboard and agent]
    F --> G
```

## Documentation
- [Coding and contribution conventions](CONTRIBUTING.md)
- [Step-by-step walkthrough and rationale](docs/project-walkthrough.md)
- [Data sources and selection](docs/data-sources.md)
- [High-Level System Design](docs/HLSD.md)
- [Low-Level Design](docs/LLD.md)
- [Silver ER diagram](docs/silver-er-diagram.md)
- [Gold star schema](docs/gold-star-schema.md)
- [Metric definitions](docs/metric-definitions.md)
- [Data quality and build results](docs/data-quality-results.md)
- [Reproduction guide](docs/reproduction.md)
- [Agent evaluation plan](docs/evaluation-plan.md)

## Source
Downloaded from the official [CFPB Consumer Complaint Database Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/). See the source document for selection rules and the distinction between source-page coverage and observed file dates.

## Repository contents
`notebooks/` contains the saved Colab workflow without execution outputs. `dbt/` contains extracted SQL models, tests and definitions. `reports/` contains small observed result files. `scripts/` provides database bootstrap support. Large datasets, database files and private runtime configuration are excluded.

## Validation
The packaged project passed a synthetic smoke build: **21 models and 126 dbt data tests**, plus edge-case assertions. The workflow in `.github/workflows/dbt-smoke.yml` repeats this check on pushes and pull requests. Full-data results remain separately documented.

## Get started
Use [the reproduction guide](docs/reproduction.md) to run entirely in Colab or run the extracted dbt project against existing bronze Parquet. Versions observed in the successful Colab environment are pinned in `requirements.txt`.

> Narrative availability varies markedly by year. Show coverage alongside AI findings; absence of published text is not absence of customer problems. This is an analysis of a downloaded snapshot, not a live complaint feed.
