# Financial Complaint Intelligence

> [!WARNING]
> **Refresh may fail — CFPB HTTP 403 (2026-10-05).** CFPB archive and API requests from the GitHub runner have returned Akamai **Access Denied** responses. Daily and automatic refresh remain enabled. If this issue occurs, the attempted update will fail and the dashboard will retain its last validated snapshot. A successful refresh requires source access and all validation gates to pass.

![Screenshot of the preserved GitHub HTTP 403 diagnostic evidence](assets/screenshots/cfpb-403-access-denied.jpg)

*Screenshot of the actual GitHub diagnostic report. [Investigation and evidence](docs/cfpb-access-diagnostics.md).*

A CFPB complaint analytics platform with an eight-tab executive dashboard, a tested rolling-refresh implementation, and a configurable Gemini business chatbot with constrained SQL and cited evidence.

## Problem statement
Financial-services leadership needs a reliable way to identify changing complaint patterns and investigate the customer experiences behind them. This project prepares consistent complaint metrics and narrative evidence for a dashboard and a data agent that can answer questions using SQL calculations and cited complaint records.

The intended decisions are which complaint categories need investigation, where volumes are changing, and how recorded response outcomes differ. Public complaints cannot establish internal root causes, customer satisfaction, company-wide incident rates or financial losses.

## Historical full-data validation
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

**Live dashboard:** [Streamlit analytics](dashboard/README.md) with eight tabs, shared date/company/product filters, issue drilldown, response outcomes, state mapping and channel comparisons. Four independently reconciled aggregate datasets supply these views.

**Implemented refresh code:** daily archive discovery, source hashing and cached downloads, rolling 36-month rebuilds, dbt validation and four-export reconciliation. Publication uses a release branch → PR → merge commit; first full-data rolling publication is blocked by a source-download HTTP 403.

**Implemented NLP:** [Complaint Insights](docs/complaint-insights.md) discovers recurring themes in filtered public narrative excerpts using local TF–IDF + NMF, with an executive briefing, source-labelled concern cards, sample counts, prior-period comparisons and supporting complaint IDs. A fifth serving Parquet holds up to 60K sampled excerpts; population-wide narrative findings are not claimed.

**AI Analyst:** whole-dashboard Gemini integration with business glossary/source documents, constrained aggregate SQL, sampled narrative retrieval, source references and exact query results. Activation requires a Gemini Free Tier key from a project without linked billing. [Setup and contracts](docs/ai-assistant.md).

**Future work:** persistent full-detail warehouse serving, semantic/vector narrative retrieval, wide/star agent benchmarks and recorded live-model evaluations. Offline tool/UI tests pass; live quality is not established until key activation and acceptance.

[Open the live executive dashboard](https://financial-complaint-intelligence.streamlit.app/)

## Architecture
The automated workflow connects public source discovery to a validated release PR and Streamlit deployment. This project combines **medallion architecture** with **two gold query structures**. Silver is shared; wide gold remains available alongside the additional star schema. The star models reuse the existing gold metric definitions rather than replacing them.

![Financial Complaint Intelligence architecture](assets/diagrams/system-architecture.svg)

The architecture draw.io file includes platform and deployment/operations pages; the LLD file adds processing, serving contracts and release lifecycle views.

[View full-size diagram](assets/diagrams/system-architecture.svg) · [Download editable draw.io file](assets/diagrams/system-architecture.drawio) · [High-Level System Design](docs/HLSD.md)

## Documentation
- [Coding and contribution conventions](CONTRIBUTING.md)
- [Step-by-step walkthrough and rationale](docs/project-walkthrough.md)
- [Data sources and selection](docs/data-sources.md)
- [High-Level System Design](docs/HLSD.md)
- [Low-Level Design](docs/LLD.md)
- [Architecture design guidance and view conventions](docs/design-guidelines.md)
- [Silver ER diagram](docs/silver-er-diagram.md)
- [Gold star schema](docs/gold-star-schema.md)
- [Metric definitions](docs/metric-definitions.md)
- [Data quality and build results](docs/data-quality-results.md)
- [Reproduction guide](docs/reproduction.md)
- [Agent evaluation plan](docs/evaluation-plan.md)
- [CFPB access investigation](docs/cfpb-access-diagnostics.md)

## Source
Downloaded from the official [CFPB Consumer Complaint Database Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/). See the source document for selection rules and the distinction between source-page coverage and observed file dates.

## Repository contents
`notebooks/` contains the saved Colab workflow without execution outputs. `dbt/` contains extracted SQL models, tests and definitions. `reports/` contains small observed result files. `scripts/` provides database bootstrap, synthetic model validation and rolling source-to-dashboard refresh. Four aggregate Parquet serving datasets and a bounded narrative evidence sample are versioned at the repository root. Large source archives, databases and private runtime configuration are excluded.

## Dashboard tabs

Overview · Trends · Companies · Products & Issues · Response Outcomes · Geography & Channels · Complaint Insights. Global filters span tabs; local issue drilldown is explicitly scoped. On-screen counts use K/M/B, and downloads keep exact values. See [dashboard operation](dashboard/README.md).

## Validation
The packaged project passed a synthetic smoke build: **21 models and 126 dbt data tests**, plus edge-case assertions. The workflow in `.github/workflows/dbt-smoke.yml` repeats this check on pushes and pull requests. Full-data results remain separately documented.

## Automated refresh

The [scheduled refresh pipeline](docs/automated-refresh.md) checks public CFPB archives daily and stages a validated rolling 36-month release on source or transformation changes. It rebuilds all dbt layers and publishes four aggregate exports and their narrative evidence sample together through a release branch, PR and merge commit. First full-data runner publication must pass before the historical dashboard snapshot is replaced. The window is anchored to the latest archive-labelled month, not the wall clock. The live Colab notebook remains the interactive development workflow.

## Get started
Use [the reproduction guide](docs/reproduction.md) to run entirely in Colab or run the extracted dbt project against existing bronze Parquet. Versions observed in the successful Colab environment are pinned in `requirements.txt`.

> Narrative availability varies markedly by year. Show coverage alongside AI findings; absence of published text is not absence of customer problems. This is an analysis of a downloaded snapshot, not a live complaint feed.


Current full-run blocker (2026-10-05): GitHub-hosted execution successfully discovered the archive catalogue and passed synthetic dbt validation, but its first source ZIP request returned HTTP 403. No refreshed datasets were published. Unattended full-data ingestion requires an allowed download path or execution environment; it is not yet operational. Existing dashboard datasets remain unchanged.
