# Reproduction guide

## Option A: Colab on an iPad
1. Download the 18 selected archive periods from the official CFPB archive; the filenames are in `reports/source_inventory.csv`.
2. Open `notebooks/01_CFPB_Data_Exploration.ipynb` in Colab. It is an output-cleared copy of the saved workflow.
3. Change the source folder path if needed. The notebook expects `/content/drive/MyDrive/Saved from Chrome` and mounts Drive interactively.
4. Execute cells in order: inventory, source selection, bronze conversion, checkpoint, profiling, staging, silver, wide gold and additional star builds.
5. Check dbt exit codes and result tables. Keep Colab connected until checkpoints finish.

Original notebook install cells use unpinned packages. For the versions observed in this run, replace them with `%pip install -r /path/to/requirements.txt` after making the repository available in Colab. Colab may contain conflicting preinstalled Google protobuf consumers; the earlier environment showed a warning while dbt itself worked. Keep future AI dependencies isolated when necessary.

## Option B: extracted dbt project with existing bronze
Run from the repository root in a Python environment with the pinned requirements installed. This path does not require regenerating model files from notebook cells.

```bash
pip install -r requirements.txt
cp dbt/profiles.example.yml dbt/profiles.yml
mkdir -p data/duckdb_temp
export FCI_DATABASE_PATH="$PWD/data/complaints.duckdb"
export FCI_TEMP_DIRECTORY="$PWD/data/duckdb_temp"
python scripts/bootstrap_bronze.py --database "$FCI_DATABASE_PATH" --parquet-pattern '/absolute/path/to/bronze/*/part-*.parquet'
dbt build --project-dir dbt --profiles-dir dbt
```

The bootstrap script registers the bronze view; it does not ingest CSVs. Full ZIP ingestion is in the notebook. Close notebook connections before launching dbt against the same database. Do not commit `profiles.yml`, the database or large data files.

To build only the added star models after silver and wide gold exist:

```bash
dbt build --project-dir dbt --profiles-dir dbt --select path:models/star
```

## Inspect weekly metrics
```sql
SELECT CAST(date_trunc('week', date_received) AS DATE) AS week_start,
       SUM(complaint_count) AS complaints,
       100.0 * SUM(timely_response_count)
           / NULLIF(SUM(known_timeliness_count), 0) AS timely_rate_pct
FROM main_gold.complaint_metrics
GROUP BY 1 ORDER BY 1;
```

## Repeatability limits
The existing notebook uses full rebuilds, development paths and completion markers without source hashing. It is not a scheduled production ingestion system. Store file checksums and source versions before introducing automated refreshes. Full-data checks were run in the user's Colab environment; repository smoke validation uses synthetic data separately from those reported counts.

## Synthetic validation without source downloads
Run `python scripts/smoke_test.py`. This creates a temporary six-record synthetic bronze table, builds every model, runs dbt assertions and checks representative edge cases. No production dataset or credentials are needed.
