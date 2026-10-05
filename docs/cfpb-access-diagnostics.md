# CFPB access investigation

Observed 2026-10-05 at 23:10 UTC from a GitHub-hosted Ubuntu runner. [Diagnostic run](https://github.com/Satyavathi-Gunturi/Financial-Complaint-Intelligence/actions/runs/37386931066). The reproducible response evidence is in [cfpb_access_diagnostic.json](../reports/cfpb_access_diagnostic.json).

## Findings

| Request | Result | Evidence |
|---|---|---|
| Narratives archive catalogue | HTTP 403 | `Server: AkamaiGHost`, HTML Access Denied, edgesuite reference |
| Exact first ZIP rejected by refresh | HTTP 403 | HTML Access Denied with an edgesuite reference |
| Official API CSV export for one received-date day | HTTP 403 | `Server: AkamaiGHost`, HTML Access Denied, edgesuite reference |

All three used the archive pipeline's honest `Financial-Complaint-Intelligence/1.0` User-Agent. Each endpoint was requested once and no more than 4096 bytes were read. The JSON evidence records selected non-secret headers and error bodies; it contains no complaint rows. No retries, browser impersonation, proxy changes, credentials or publication were used.

## What this establishes

The current requests are denied at CFPB's Akamai delivery/access layer before the pipeline parses CSV, builds DuckDB or runs dbt. This is an access failure, not a transformation or Parquet-size failure. A valid API route does not independently resolve access from this runner: the tested API request was also denied. The observed rejection does not establish that public complaint downloads are prohibited.

The exact Akamai policy is not exposed in the error. IP reputation, request classification and other access policy possibilities remain hypotheses. The original refresh catalogue request used urllib's default User-Agent and succeeded; the later diagnostic used the archive User-Agent for all three endpoints on a different runner at a later time. These tests do not isolate which difference caused the catalogue result to change, or prove that every GitHub runner is blocked.

## Supported next steps

Obtain CFPB guidance or provider-approved programmatic access using the exact URL, timestamp, User-Agent and Akamai reference in this evidence. If a documented access path or an authorized execution environment is provided, test a bounded request there before changing the refresh source. A different runner alone is not a proven fix. No request fingerprint or network changes should be used to evade the rejection.

Once access is established, validate the complete retained-window ingestion, all dbt tests, four export totals and release PR merge. Until then the live dashboard retains the historical snapshot and no unattended data refresh is claimed.

## API and narrative constraints

The [current API release notes](https://cfpb.github.io/api/ccdb/release-notes.html) state that filtered exports are CSV-only with a 100,000-complaint cap, and that complaint narratives were removed from the current database in September 2026. The [CFPB announcement](https://www.consumerfinance.gov/about-us/newsroom/the-cfpb-to-cease-discretionary-publication-of-complaint-narratives-and-visualizations/) explains that previously published narratives were disclosed through the FOIA Reading Room. An API migration would therefore need a separate source/coverage contract for historical narrative evidence; it cannot promise continuing new narrative publication.

## Repeat the diagnostic

Use the manual **CFPB access diagnostics** workflow for a deliberate authorized check, or run `python scripts/diagnose_cfpb_access.py` in the execution environment under investigation. The workflow also runs when its script or workflow is changed in a PR. HTTP rejection is recorded as evidence rather than failing the diagnostic job; a green diagnostic check means evidence collection completed, not that source access succeeded. Artifacts expire after 14 days; the versioned report preserves this observed result.
