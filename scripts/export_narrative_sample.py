"""Create a bounded narrative evidence export from a validated DuckDB checkpoint."""

import argparse
import hashlib
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
from narrative_analysis import redact  # noqa: E402


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_sample(database, overview, output, limit=60000):
    """Global deterministic hash sample, not stratified or population theme counts."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database), read_only=True) as con:
        con.execute("SET memory_limit='1GB'")
        con.execute("SET threads=2")
        expected = con.execute(
            """SELECT SUM(complaint_count), SUM(narrative_count),
            MIN(date_received), MAX(date_received) FROM read_parquet(?)""",
            [str(overview)],
        ).fetchone()
        actual = con.execute("""SELECT COUNT(*), SUM(narrative_count), MIN(date_received),
            MAX(date_received) FROM main_gold.complaint_metrics""").fetchone()
        if expected != actual:
            raise ValueError(
                "Checkpoint does not match the dashboard overview snapshot"
            )
        corpus = con.execute("""SELECT COUNT(*) FROM main_silver.complaint_narratives
            WHERE length(trim(narrative)) > 0""").fetchone()[0]
        if corpus != int(actual[1]):
            raise ValueError("Narrative view does not reconcile to narrative_count")
        con.execute(
            """CREATE TEMP TABLE selected_narratives AS
            SELECT complaint_id, left(narrative, 2000) AS excerpt,
            length(narrative) > 2000 AS excerpt_truncated
            FROM main_silver.complaint_narratives WHERE length(trim(narrative)) > 0
            ORDER BY md5(complaint_id), complaint_id LIMIT ?""",
            [limit],
        )
        frame = con.execute("""SELECT m.complaint_id, m.date_received, m.company_name,
            m.product, m.sub_product, m.issue, m.state, m.company_response,
            n.excerpt, n.excerpt_truncated FROM main_gold.complaint_metrics m
            JOIN selected_narratives n ON m.complaint_id = n.complaint_id
            ORDER BY md5(m.complaint_id), m.complaint_id""").fetchdf()
    frame["excerpt"] = frame["excerpt"].map(redact)
    frame["corpus_narratives"] = corpus
    frame["overview_sha256"] = file_hash(overview)
    frame["sample_method"] = "global_md5_id_v1"
    frame["exported_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    # Keep the same hash-ranked prefix when reducing the sample to respect upload limits.
    target = output.with_suffix(".tmp.parquet")
    while True:
        frame.to_parquet(target, index=False, compression="zstd")
        if target.stat().st_size < 24 * 1024**2:
            break
        if len(frame) <= 1000:
            target.unlink()
            raise ValueError("Narrative evidence exceeds serving size guard")
        frame = frame.iloc[: len(frame) // 2].copy()
    with duckdb.connect() as con:
        rows, ids = con.execute(
            "SELECT COUNT(*), COUNT(DISTINCT complaint_id) FROM read_parquet(?)",
            [str(target)],
        ).fetchone()
    if rows != ids:
        target.unlink()
        raise ValueError("Duplicate complaint IDs in evidence export")
    target.replace(output)
    print(
        f"{output.name}: {rows:,} sampled narratives / {corpus:,} available; "
        f"{output.stat().st_size / 1024**2:.2f} MB; unique IDs verified"
    )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument(
        "--overview",
        type=Path,
        default=ROOT / "dashboard_daily_company_product.parquet",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dashboard_narratives.parquet"
    )
    parser.add_argument("--limit", type=int, default=60000)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    export_sample(args.database, args.overview, args.output, args.limit)
