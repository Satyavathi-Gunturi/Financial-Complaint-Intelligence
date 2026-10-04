# Low-Level Design (LLD)

**Engineering view:** physical schemas, field-level contracts, key construction, metric algebra and quality gates.

![Technical design diagram](../assets/diagrams/low-level-contracts.svg)

[Open the full-size diagram](../assets/diagrams/low-level-contracts.svg) · [Project walkthrough](project-walkthrough.md) · [Metric definitions](metric-definitions.md)

---

## Engineering invariants

| Invariant | Design rule | Validation |
|---|---|---|
| Complaint grain | One source complaint per fact row | Unique ID + row-preservation tests |
| Identity | Source ID as text; JSON-based category keys | Key uniqueness + relationship tests |
| Missingness | Optional blanks become NULL | Required-field and outcome-partition tests |
| Metrics | Additive 0/1 flags; aggregate before division | Binary and consistency tests |
| Time | Received date default; Monday weeks; two calendar roles | Date key relationships + ISO-boundary smoke assertion |
| Evidence | Preserve nonblank narrative text | Narrative-count preservation |
| Parallel gold | Identical metric definitions in wide and star | Row and every-flag total reconciliation |

## Physical schemas
| Schema | Objects |
|---|---|
| `main` | `bronze_complaints` view over selected Parquet parts |
| `main_staging` | cleaned complaint view, keyed view and split-tag view |
| `main_silver` | eight materialized relational tables |
| `main_gold` | materialized `complaint_metrics`, narrative search view |
| `main_star` | materialized fact and seven dimensions |

Names follow dbt's default `<profile_schema>_<custom_schema>` behavior. The development profile starts at `main`.

## Ingestion contract
Read selected ZIP CSV members in 50,000-row pandas chunks with string types and `keep_default_na=False`. Preserve original 16 fields, write Zstandard Parquet, and add `_source_archive`, `_source_csv`, `_source_record_number` and `_ingested_at`. Record numbers are logical CSV records, not physical lines. Count written Parquet rows against read rows. `_SUCCESS.json` markers support completed-source reuse in the same output folder but do not validate a changed source checksum. Partial parts are removed on retry for an unfinished source.

## Staging contract
Trim ordinary categorical fields and translate empty strings to NULL. Keep complaint ID and ZIP as text. Parse received/sent dates as ISO dates or `%m/%d/%Y`. Map `Yes`/`No` timeliness to booleans. Preserve nonempty narrative text verbatim; whitespace-only text becomes NULL. No date or complaint filters apply. Staging preserves raw sent-date and timeliness strings for diagnosis.

## Keys and cardinality
Complaint ID is the verified unique source key. Category keys use MD5 over JSON-encoded value lists; JSON preserves component boundaries and NULLs. Keys are stable for unchanged labels but are not enterprise master-data identifiers. Uniqueness tests catch observed collisions or inconsistencies.

Product key: product + sub-product. Issue key: product + sub-product + issue + sub-issue. Geography key: state + ZIP. Response key: outcome + public response category + timeliness string. Blank optional labels remain NULL attributes while category combination keys remain populated.

Silver tags split on commas, trim and deduplicate complaint/tag pairs. Two tags produce 484,025 relationships; joining this bridge before aggregation can multiply complaints. Use EXISTS filters or deduplicate complaint IDs when filtering tags.

## Gold designs
Wide gold joins silver dimensions with LEFT JOINs and retains one row per complaint plus integer metric flags. The narrative view joins complaint context to available narratives. It is not a vector index.

The additional star schema reads the existing wide model and preserves its flags exactly. Date keys are integer YYYYMMDD. A continuous calendar spans received and sent dates. Date is role-playing: received and sent keys point to the same calendar. ISO year and ISO week must be used together; week starts Monday. Gold issue dimension has product context as attributes but no product-dimension FK.

## Tests
SQL/YAML tests verify unique/non-null keys, required fields, dimension relationships, row preservation, narrative preservation, unique tag pairs, product/issue consistency, binary flags, flag partitions and star/wide metric reconciliation. These are dbt assertions; DuckDB tables are not declared with enforced SQL primary-key/foreign-key constraints. Tests must run after transformations.

## Planned agent tool contracts
`query_metrics(question, structure, filters)` will select either wide or star schema, execute validated read-only SQL with row/time limits, and return columns, rows, query and metric context. `search_narratives(query, filters)` will retrieve complaint IDs, source context and supporting text. These are proposed contracts, not implemented functions.

Cross-tool date/company filters must match. Answers should identify snapshot coverage and distinguish counts, response categories and narrative findings. Both structures will be evaluated against identical question definitions and ground-truth SQL.

## Recovery and portability
Use `scripts/bootstrap_bronze.py` to bind available Parquet to `main.bronze_complaints`; close other database connections before dbt starts. Profiles use environment-configurable paths. Colab notebook generators still contain the original Colab/Drive paths. Drive-mounted sources must be mounted again after restart. A database backup is copied after connections close; large data stays outside GitHub.
