"""Discover CFPB archive changes and build a validated rolling dashboard release."""

import argparse
import calendar
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import duckdb
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAGE = "https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/"
EXPORTS = {
    "dashboard_daily_company_product.parquet": [],
    "dashboard_issues.parquet": ["issue", "sub_issue"],
    "dashboard_geography.parquet": ["state"],
    "dashboard_channels.parquet": ["submission_channel"],
}
BASE_FIELDS = [
    "date_received",
    "company_id",
    "company_name",
    "product_category_id",
    "product",
    "sub_product",
]
RAW_FIELDS = [
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Consumer complaint narrative",
    "Company public response",
    "Company",
    "State",
    "ZIP code",
    "Tags",
    "Submitted via",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Complaint ID",
]


def digest(path):
    """Hash bytes without loading an archive into memory."""
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def month_offset(value, amount):
    """Shift a calendar month without approximating years as day counts."""
    number = value.year * 12 + value.month - 1 + amount
    return date(number // 12, number % 12 + 1, 1)


def archive_period(filename):
    """Fail closed if CFPB's archive naming convention changes."""
    match = re.fullmatch(r"CCDB_Export_(\d+)_(.+)\.zip", filename, re.I)
    if not match:
        raise ValueError(f"Unrecognized archive name: {filename}")
    label = match[2].replace("_", " ")
    endpoints = label.split(" through ")
    if len(endpoints) > 2:
        raise ValueError(f"Ambiguous archive period: {filename}")
    months = {
        name.lower(): index for index, name in enumerate(calendar.month_name) if name
    }
    last_year = re.findall(r"\b(20\d{2})\b", label)
    if not last_year:
        raise ValueError(f"Archive lacks year: {filename}")
    result = []
    for endpoint in endpoints:
        tokens = endpoint.lower().split()
        if tokens[0] not in months:
            raise ValueError(f"Unknown archive month: {filename}")
        years = re.findall(r"\b(20\d{2})\b", endpoint)
        result.append(
            date(int(years[0] if years else last_year[-1]), months[tokens[0]], 1)
        )
    if len(result) == 1:
        result.append(result[0])
    if result[0] > result[1]:
        raise ValueError(f"Invalid archive interval: {filename}")
    return int(match[1]), result[0], result[1]


class ArchiveLinks(HTMLParser):
    """Collect only official HTTPS archive links; never execute source HTML."""

    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        url = urllib.parse.urljoin(SOURCE_PAGE, href)
        parsed = urllib.parse.urlparse(url)
        name = Path(urllib.parse.unquote(parsed.path)).name
        if name.startswith("CCDB_Export_") and name.lower().endswith(".zip"):
            if parsed.scheme != "https" or parsed.hostname not in {
                "files.consumerfinance.gov",
                "www.consumerfinance.gov",
            }:
                raise ValueError(
                    "Archive link is outside the official source allowlist"
                )
            self.links.add(url)


def discover(html):
    """Select archive intervals covering the latest published 36 calendar months."""
    parser = ArchiveLinks()
    parser.feed(html)
    if not parser.links:
        raise ValueError("No CFPB archive links found; publishing is blocked")
    sources = []
    for url in sorted(parser.links):
        name = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
        priority, first, last = archive_period(name)
        sources.append(
            dict(url=url, name=name, priority=priority, first=first, last=last)
        )
    last_month = max(item["last"] for item in sources)
    start = month_offset(last_month, -35)
    end = month_offset(last_month, 1)
    selected = [
        item for item in sources if item["last"] >= start and item["first"] < end
    ]
    if len({item["name"] for item in selected}) != len(selected):
        raise ValueError("Duplicate archive filenames at different URLs")
    covered = set()
    for item in selected:
        point = max(start, item["first"])
        while point <= item["last"]:
            covered.add(point)
            point = month_offset(point, 1)
    if any(month_offset(start, offset) not in covered for offset in range(36)):
        raise ValueError("Archive catalog has gaps in the rolling window")
    return sorted(selected, key=lambda item: item["priority"]), start, end


def download(source, cache, previous):
    """Conditional downloads plus SHA-256 verify cached archive identity."""
    target = cache / source["name"]
    old = previous.get(source["url"], {})
    headers = {"User-Agent": "Financial-Complaint-Intelligence/1.0"}
    if target.exists() and old.get("sha256") == digest(target):
        if old.get("etag"):
            headers["If-None-Match"] = old["etag"]
        elif old.get("last_modified"):
            headers["If-Modified-Since"] = old["last_modified"]
    request = urllib.request.Request(source["url"], headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            final = urllib.parse.urlparse(response.url)
            if final.scheme != "https" or final.hostname not in {
                "files.consumerfinance.gov",
                "www.consumerfinance.gov",
            }:
                raise ValueError("Unexpected archive redirect")
            partial = target.with_suffix(".partial")
            with partial.open("wb") as stream:
                shutil.copyfileobj(response, stream, length=1024 * 1024)
            partial.replace(target)
            validators = {
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except urllib.error.HTTPError as exc:
        if (
            exc.code != 304
            or not target.exists()
            or old.get("sha256") != digest(target)
        ):
            raise
        validators = {
            "etag": old.get("etag"),
            "last_modified": old.get("last_modified"),
        }
    if not zipfile.is_zipfile(target):
        raise ValueError(f"Invalid ZIP downloaded: {source['name']}")
    return dict(
        url=source["url"], name=source["name"], sha256=digest(target), **validators
    )


def ingest(sources, cache, bronze, start, end):
    """Stream selected archive CSVs and exclude records outside retention."""
    bronze.mkdir(parents=True)
    now = datetime.now(timezone.utc).isoformat()
    retained = 0
    for source in sources:
        with zipfile.ZipFile(cache / source["name"]) as archive:
            members = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(members) != 1:
                raise ValueError(f"Expected one CSV in {source['name']}")
            record = 0
            with archive.open(members[0]) as stream:
                for batch, chunk in enumerate(
                    pd.read_csv(
                        stream, dtype="string", keep_default_na=False, chunksize=50000
                    )
                ):
                    if not set(RAW_FIELDS).issubset(chunk.columns):
                        raise ValueError("Required source columns changed")
                    parsed = pd.to_datetime(
                        chunk["Date received"], format="mixed", errors="coerce"
                    )
                    if (
                        parsed.isna().any()
                        or chunk["Complaint ID"].str.strip().eq("").any()
                    ):
                        raise ValueError(
                            "Source has invalid dates or missing complaint IDs"
                        )
                    chunk["_source_record_number"] = range(
                        record + 1, record + len(chunk) + 1
                    )
                    record += len(chunk)
                    chunk = chunk.loc[
                        (parsed >= pd.Timestamp(start)) & (parsed < pd.Timestamp(end))
                    ].copy()
                    if chunk.empty:
                        continue
                    chunk["_source_archive"] = source["name"]
                    chunk["_source_csv"] = members[0]
                    chunk["_ingested_at"] = now
                    chunk["_source_priority"] = source["priority"]
                    chunk.to_parquet(
                        bronze / f"{source['priority']}-{batch}.parquet",
                        compression="zstd",
                        index=False,
                    )
                    retained += len(chunk)
    if not retained:
        raise ValueError("No retained complaints; publishing blocked")
    return retained


def build_database(work, start, end):
    """Deduplicate by release ordinal and build all maintained dbt models/tests."""
    database = work / "complaints.duckdb"
    with duckdb.connect(str(database)) as con:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET temp_directory=?", [str(work / "spill")])
        con.read_parquet(
            str(work / "bronze/*.parquet"), union_by_name=True
        ).create_view("incoming")
        duplicates = con.execute(
            'SELECT COUNT(*) - COUNT(DISTINCT trim("Complaint ID")) FROM incoming'
        ).fetchone()[0]
        # A higher numbered CFPB release takes precedence across overlapping exports.
        con.execute(
            'CREATE TABLE bronze_complaints AS SELECT * EXCLUDE (_source_priority) FROM incoming QUALIFY row_number() OVER (PARTITION BY trim("Complaint ID") ORDER BY _source_priority DESC, _source_record_number DESC) = 1'
        )
    profile_dir = work / "profiles"
    profile_dir.mkdir()
    profile = yaml.safe_load((ROOT / "dbt/profiles.example.yml").read_text())
    (profile_dir / "profiles.yml").write_text(yaml.safe_dump(profile))
    env = dict(
        os.environ,
        FCI_DATABASE_PATH=str(database),
        FCI_TEMP_DIRECTORY=str(work / "spill"),
    )
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(ROOT / "dbt"),
            "--profiles-dir",
            str(profile_dir),
        ],
        check=True,
        env=env,
    )
    with duckdb.connect(str(database), read_only=True) as con:
        outside = con.execute(
            "SELECT COUNT(*) FROM main_gold.complaint_metrics WHERE date_received < ? OR date_received >= ?",
            [start, end],
        ).fetchone()[0]
        if outside:
            raise ValueError("Retention validation failed")
    return database, duplicates


def export_datasets(database, output, start, end):
    """Reconcile every additive flag independently for all four export grains."""
    output.mkdir(exist_ok=True, parents=True)
    results = {}
    with duckdb.connect(str(database), read_only=True) as con:
        columns = con.execute("DESCRIBE main_gold.complaint_metrics").fetchdf()[
            "column_name"
        ]
        metrics = [c for c in columns if c.endswith("_count")]
        sums = ", ".join(f'SUM("{c}") AS "{c}"' for c in metrics)
        expected = con.execute(
            f"SELECT {sums} FROM main_gold.complaint_metrics"
        ).fetchone()
        dates = con.execute(
            "SELECT MIN(date_received), MAX(date_received), COUNT(*) FROM main_gold.complaint_metrics"
        ).fetchone()
        for filename, extra in EXPORTS.items():
            fields = ", ".join(f'"{c}"' for c in BASE_FIELDS + extra)
            target = output / filename
            escaped = str(target).replace("'", "''")
            con.execute(
                f"COPY (SELECT {fields}, {sums} FROM main_gold.complaint_metrics GROUP BY ALL) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            actual = con.execute(
                f"SELECT {sums} FROM read_parquet(?)", [str(target)]
            ).fetchone()
            if actual != expected:
                raise ValueError(f"Metric totals differ in {filename}")
            if target.stat().st_size >= 90 * 1024**2:
                raise ValueError("Export exceeds repository serving size guard")
            results[filename] = dict(sha256=digest(target), bytes=target.stat().st_size)
    return dict(
        window_start=start.isoformat(),
        window_end_exclusive=end.isoformat(),
        observed_first_date=dates[0].isoformat(),
        observed_last_date=dates[1].isoformat(),
        complaints=dates[2],
        metric_totals={name: int(value) for name, value in zip(metrics, expected)},
        exports=results,
    )


def main():
    """Publish-ready outputs are staged; only the workflow commits them atomically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    work = ROOT / "data/refresh_work"
    cache = ROOT / "data/source_cache"
    output = ROOT / "data/release"
    cache.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_PAGE, timeout=60) as response:
        sources, start, end = discover(response.read().decode("utf-8"))
    print(
        f"Source window: {start} through {end} (exclusive); {len(sources)} archives",
        flush=True,
    )
    if args.check_only:
        print(
            json.dumps([dict(name=s["name"], url=s["url"]) for s in sources], indent=2)
        )
        return
    previous_path = ROOT / "reports/refresh_manifest.json"
    old = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    previous = {item["url"]: item for item in old.get("sources", [])}
    records = []
    for source in sources:
        print(f"Checking {source['name']}", flush=True)
        records.append(download(source, cache, previous))
    revision = hashlib.sha256()
    revision.update(json.dumps([(s["url"], s["sha256"]) for s in records]).encode())
    revision.update(f"{start}/{end}".encode())
    # Transformation changes also require a new release even with unchanged inputs.
    for path in sorted((ROOT / "dbt").rglob("*")) + [
        Path(__file__),
        ROOT / "requirements-refresh.txt",
        ROOT / "scripts/export_narrative_sample.py",
        ROOT / "dashboard/narrative_analysis.py",
    ]:
        if (
            path.is_file()
            and "target" not in path.parts
            and "logs" not in path.parts
            and path.name != "profiles.yml"
        ):
            revision.update(str(path.relative_to(ROOT)).encode())
            revision.update(path.read_bytes())
    fingerprint = revision.hexdigest()
    if fingerprint == old.get("revision") and not args.force:
        print(
            "Source and transformation revision unchanged; no rebuild or publication."
        )
        return
    for path in (work, output):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
    if shutil.disk_usage(work).free < 12 * 1024**3:
        raise RuntimeError("At least 12 GiB free disk required for full-data refresh")
    ingest(sources, cache, work / "bronze", start, end)
    database, duplicates = build_database(work, start, end)
    metadata = export_datasets(database, output, start, end)
    from export_narrative_sample import export_sample

    evidence = export_sample(
        database,
        output / "dashboard_daily_company_product.parquet",
        output / "dashboard_narratives.parquet",
    )
    metadata["exports"][evidence.name] = dict(
        sha256=digest(evidence), bytes=evidence.stat().st_size
    )
    metadata.update(
        revision=fingerprint,
        sources=records,
        overlap_records_removed=duplicates,
        validated_at=datetime.now(timezone.utc).isoformat(),
        retention_months=36,
        status="validated",
        window_anchor="latest archive-labelled month",
    )
    (output / "refresh_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Release staged after dbt tests and four-export metric reconciliation.")


if __name__ == "__main__":
    main()
