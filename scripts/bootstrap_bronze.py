"""Register existing bronze Parquet in DuckDB; no CSV ingestion or data copy."""
import argparse
import glob
from pathlib import Path
import duckdb

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--parquet-pattern', required=True)
    args = parser.parse_args()
    if not glob.glob(args.parquet_pattern, recursive=True):
        parser.error('No Parquet files match the supplied pattern')
    Path(args.database).parent.mkdir(parents=True, exist_ok=True)
    pattern = args.parquet_pattern.replace("'", "''")
    with duckdb.connect(args.database) as con:
        con.execute(f"CREATE OR REPLACE VIEW main.bronze_complaints AS SELECT * FROM read_parquet('{pattern}', union_by_name=true)")
        count = con.execute('SELECT COUNT(*) FROM main.bronze_complaints').fetchone()[0]
    print(f'Registered {count:,} bronze records in {args.database}')

if __name__ == '__main__':
    main()
