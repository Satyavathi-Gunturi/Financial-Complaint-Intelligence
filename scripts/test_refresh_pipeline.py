"""Exercise rolling retention, revised records, dbt builds and export reconciliation."""

import csv
import io
import json
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import duckdb
from refresh_pipeline import (
    RAW_FIELDS,
    archive_period,
    build_database,
    discover,
    export_datasets,
    ingest,
)


def fixture(path, rows):
    """Write a small source-shaped archive; never copy production narratives."""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=RAW_FIELDS)
    writer.writeheader()
    for complaint_id, received, company in rows:
        row = dict.fromkeys(RAW_FIELDS, "")
        row.update(
            {
                "Complaint ID": complaint_id,
                "Date received": received,
                "Company": company,
                "Product": "Credit card",
                "Sub-product": "General",
                "Issue": "Payment",
                "State": "TX",
                "ZIP code": "001XX",
                "Submitted via": "Web",
                "Date sent to company": received,
                "Timely response?": "Yes",
                "Company response to consumer": "Closed with explanation",
                "Consumer complaint narrative": "Synthetic fixture narrative",
            }
        )
        writer.writerow(row)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(path.stem + ".csv", stream.getvalue())


def main():
    """Test a complete small refresh, including revised ID precedence."""
    assert archive_period("CCDB_Export_21_August_2026.zip")[2] == date(2026, 8, 1)
    html = '<a href="https://files.consumerfinance.gov/f/documents/CCDB_Export_1_January_2023_through_August_2026.zip">Archive</a>'
    sources, start, end = discover(html)
    assert (start, end) == (date(2023, 9, 1), date(2026, 9, 1))
    next_html = (
        html
        + '<a href="https://files.consumerfinance.gov/f/documents/CCDB_Export_2_September_2026.zip">New</a>'
    )
    assert discover(next_html)[1:] == (date(2023, 10, 1), date(2026, 10, 1))
    try:
        discover(
            '<a href="https://files.consumerfinance.gov/f/documents/CCDB_Export_21_August_2026.zip">Missing months</a>'
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Missing catalog months were accepted")
    with tempfile.TemporaryDirectory(prefix="fci-refresh-test-") as temp:
        root = Path(temp)
        cache = root / "cache"
        cache.mkdir()
        fixture(
            cache / sources[0]["name"],
            [
                ("old", "2023-08-31", "Company A"),
                ("1", "2023-09-01", "Company A"),
                ("2", "08/31/2026", "Company B"),
                ("future", "2026-09-01", "Company A"),
            ],
        )
        revised = dict(sources[0], name="CCDB_Export_2_August_2026.zip", priority=2)
        fixture(cache / revised["name"], [("2", "2026-08-31", "Revised Company")])
        work = root / "work"
        work.mkdir()
        assert ingest(sources + [revised], cache, work / "bronze", start, end) == 3
        database, duplicates = build_database(work, start, end)
        assert duplicates == 1
        with duckdb.connect(str(database), read_only=True) as con:
            assert (
                con.execute(
                    "SELECT COUNT(*) FROM main_gold.complaint_metrics"
                ).fetchone()[0]
                == 2
            )
            assert (
                con.execute(
                    "SELECT company_name FROM main_gold.complaint_metrics WHERE complaint_id='2'"
                ).fetchone()[0]
                == "Revised Company"
            )
        result = export_datasets(database, root / "release", start, end)
        assert result["complaints"] == 2
        assert len(result["exports"]) == 4
        assert result["metric_totals"]["narrative_count"] == 2
        # Revised file contents affect hashes used by release identity.
        from refresh_pipeline import digest

        first = digest(cache / revised["name"])
        fixture(cache / revised["name"], [("2", "2026-08-31", "Another revision")])
        assert digest(cache / revised["name"]) != first
        print(
            json.dumps(dict(tests="passed", exports=4, retained=2, overlap_removed=1))
        )


if __name__ == "__main__":
    main()
