# High-Level System Design (HLSD)

The system prepares public CFPB complaint data for a six-tab leadership dashboard and a future evidence-backed AI agent. The scheduled refresh implementation replaces manual dataset uploads; Colab remains the interactive development and recovery environment.

![System architecture](../assets/diagrams/system-architecture.svg)

[Editable draw.io architecture](../assets/diagrams/system-architecture.drawio) · [Refresh operation guide](automated-refresh.md) · [Low-Level Design](LLD.md)

## Components and current status

| Component | Responsibility | Status |
|---|---|---|
| CFPB archive discovery | Find official ZIPs and their labelled month coverage | Live catalog discovery verified |
| GitHub Actions refresh | Daily check, manual force run, source caching and full retained-window rebuild | Implemented; initial full-data publication acceptance pending |
| DuckDB + dbt | Bronze identity, typed staging, eight silver tables, wide gold and parallel star schema | Implemented; 21 models and 126 tests pass on synthetic refresh fixtures |
| Publication gate | Reconcile four datasets, create release branch, PR and merge commit | Implemented; merge depends on repository permissions and branch rules |
| Streamlit Community Cloud | Serve filters, charts, comparisons and downloads | Live six-tab dashboard |
| Colab + Drive | Interactive work and manually saved full-data recovery checkpoints | Existing development workflow |
| SQL agent + narrative retrieval + LLM | Compute answers and cite supporting complaint records | Planned; no deployed AI agent |

## Refresh lifecycle

The scheduler checks at 11:23 UTC daily, or on an authorized manual run. Official archive URLs, byte hashes, retention boundaries and transformation code determine a release revision. Conditional HTTP requests reuse verified ZIPs where supported. Unchanged revisions skip the build and publication.

A changed revision starts from a fresh retained-window database. The first implementation performs a complete rebuild, not incremental warehouse merges. Provenance survives ingestion. Overlapping complaint IDs resolve by higher numeric source release priority. dbt materializes staging, silver, wide gold and star models and runs the data tests. Four independent aggregate grains are then exported and their additive flags reconciled to wide gold.

All serving files and the source manifest form one release commit on an automated branch. A PR records validation and is merged using a merge commit when repository rules permit. Failed processing or a blocked PR merge preserves the last published serving files. New main-branch refresh runs supersede older runs. No implementation or data release should push directly to main.

## Rolling retention

The active window covers 36 calendar months ending in the latest archive-labelled month. August 2026 gives `[2023-09-01, 2026-09-01)`; September advances it to `[2023-10-01, 2026-10-01)`. Complaint **received date** controls retention. Expired records are absent from the newly built silver, gold, star and dashboard aggregates. Source caches, Git history and existing Drive backups are distinct from active serving retention.

The initial dashboard still represents the historical November 2022–August 2026 dataset until the first full rolling release passes. Archive labels and measured file dates are different evidence; the publication manifest records observed coverage, and a label alone does not prove a complete latest month.

## Dashboard and serving boundary

| Tab | Main questions | Dataset |
|---|---|---|
| Overview | Volume, coverage and leading concentrations | Daily company/product |
| Trends | Time patterns and equal-length previous-period change | Daily company/product |
| Companies | Company volume share and recorded response rates | Daily company/product |
| Products & Issues | Product treemap and issue/sub-issue drilldown | Daily company/product + issue aggregate |
| Response Outcomes | Timeliness and recorded relief/outcome mix | Daily company/product |
| Geography & Channels | State patterns and submission-channel volume | State + channel aggregates |

Date, company, product and sub-product filters apply across tabs. Local issue selection affects only its drilldown charts. The files are queried separately: joining different aggregate grains would multiply complaints. Cache keys include dataset file identity. The manifest adds last validated refresh and observed coverage. Display values use K/M/B while CSVs retain exact counts.

## Planned AI boundary

The AI agent will combine constrained read-only SQL with filtered narrative retrieval and an LLM. Numerical answers must come from executed calculations; narrative explanations must cite supporting complaint IDs. Detailed-data hosting, model/provider, retrieval index and evaluations are not yet implemented. The aggregate dashboard files do not contain narrative text and cannot alone support that evidence layer.

## Operations and limitations

GitHub stores code, designs and compact serving releases. Source ZIP caches are disposable; the runner's bronze and full DuckDB files are temporary. Build evidence artifacts have 14-day retention. Durable source-version storage and permanent detailed-data serving are future work. Drive backups remain untouched.

Repository permissions must permit bot PR creation. GITHUB_TOKEN-created PRs do not trigger independent Actions CI; the refresh job validates before creating them. Required checks/reviews can leave a release PR pending. GitHub schedules may be delayed or disabled after 60 days without repository activity. CFPB release timing is outside this system's control. Source/schema changes fail closed. The dashboard is a public complaint snapshot, not a live operational backlog or an incident-rate comparison adjusted for company size.


Current full-run blocker (2026-10-05): GitHub-hosted execution successfully discovered the archive catalogue and passed synthetic dbt validation, but its first source ZIP request returned HTTP 403. No refreshed datasets were published. Unattended full-data ingestion requires an allowed download path or execution environment; it is not yet operational. Existing dashboard datasets remain unchanged.
