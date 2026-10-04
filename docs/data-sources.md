# Data sources and selection

## Authoritative source
- [CFPB Consumer Complaint Database Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/): the source used for the selected narrative-bearing archive ZIPs.
- [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/): background and general complaint database access.
- Notebook snapshot retrieved and reviewed on 2026-10-04. Original download timestamps and exact file hashes were not recorded; this is not a claimed download date.

## Selection
The notebook discovered 20 CSV entries across ZIP files, retained 18 distinct `CCDB_Export_*.zip` archive entries, skipped one August 2026 duplicate copy and excluded the separate `complaints.csv.zip` export. The separate export had 15 columns and no narrative column; selected archive exports have 16 original columns including `Consumer complaint narrative`.

The selected periods span November 2022–August 2026 and contain all 2023–2025 records in these exports. No complaint sampling or date exclusion was applied. The source inventory is in [source_inventory.csv](../reports/source_inventory.csv).

Duplicate-file selection used CSV member name, uncompressed size and ZIP CRC metadata. That is not a cryptographic proof of byte equality. Subsequent full-data profiling found no duplicate complaint IDs across selected records.

## Coverage
Observed data contains 14,482,997 distinct complaint IDs, received dates 2022-11-01 through 2026-08-31, and 2,711,935 nonblank narratives. Bronze has 299 parts totaling approximately 733 MB.

The archive webpage describes previously published complaints received through August 14, 2026. The actual selected records profile through August 31, 2026. Both facts are documented rather than silently treating the webpage description as the files' measured date range. The reason for the difference has not been established.

## Limits
Narratives are not available for every complaint, and coverage falls substantially in the 2026 exports. This observation is not a diagnosis of why availability changed. Neither narrative-bearing complaints nor all published complaints establish population-wide rates of consumer harm. Company name is a source label; entity mergers are not inferred. Response outcomes represent the recorded export snapshot, not a full status history. ZIP codes may be masked and are retained as text. No private customer account records, internal root-cause labels, resolution timestamps or loss amounts are available.

## Storage
Drive currently holds source files and checkpoints. It is not the intended deployed application's permanent data service. Data hosting remains undecided; GitHub stores code and small reports, not the large source ZIPs, Parquet or DuckDB database.
