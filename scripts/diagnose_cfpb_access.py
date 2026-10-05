"""Collect bounded, read-only CFPB access evidence from the workflow runner.

Use the pipeline's honest User-Agent and one GET per endpoint. No retries,
credential changes, browser impersonation, proxy changes or full ZIP download.
Only error bodies and the CSV header are recorded, not complaint records.
"""

import csv
import io
import json
import platform
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "Financial-Complaint-Intelligence/1.0"
ARCHIVE = "https://files.consumerfinance.gov/f/documents/CCDB_Export_5_September_2023_through_March_2024.zip"
CATALOGUE = "https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/"
API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
SAFE_HEADERS = {
    "server",
    "content-type",
    "content-length",
    "content-range",
    "accept-ranges",
    "location",
    "retry-after",
    "via",
    "x-cache",
    "x-amz-cf-id",
    "x-amz-cf-pop",
    "x-amz-request-id",
    "x-amz-id-2",
    "cf-ray",
    "date",
}


def inspect(name, url):
    """Read at most 4 KiB; preserve status and selected non-secret headers."""
    evidence = {"name": name, "request_url": url, "user_agent": USER_AGENT}
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as exc:
        response = exc
    except (urllib.error.URLError, TimeoutError) as exc:
        evidence["transport_error"] = str(exc)
        return evidence
    with response:
        evidence["status"] = response.code
        evidence["final_url"] = response.url
        evidence["headers"] = {
            key: value
            for key, value in response.headers.items()
            if key.lower() in SAFE_HEADERS
        }
        sample = response.read(4096)
        evidence["bytes_sampled"] = len(sample)
        if response.code >= 400:
            evidence["error_body_excerpt"] = sample.decode("utf-8", errors="replace")
        elif name == "archive":
            evidence["zip_signature"] = sample[:4].hex()
            evidence["looks_like_zip"] = sample.startswith(b"PK\x03\x04")
        elif name == "api_csv":
            lines = sample.decode("utf-8-sig", errors="replace").splitlines()
            first_line = lines[0] if lines else ""
            evidence["csv_header"] = next(csv.reader(io.StringIO(first_line)))
    return evidence


def main():
    """Write evidence even when an endpoint rejects the request."""
    query = urllib.parse.urlencode(
        {
            "format": "csv",
            "date_received_min": "2026-09-01",
            "date_received_max": "2026-09-02",
            "no_aggs": "true",
            "no_highlight": "true",
        }
    )
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "scope": "One GET per endpoint; at most 4096 response bytes each",
        "requests": [],
    }
    for name, url in [
        ("catalogue", CATALOGUE),
        ("archive", ARCHIVE),
        ("api_csv", API + "?" + query),
    ]:
        evidence = inspect(name, url)
        report["requests"].append(evidence)
        print(json.dumps(evidence, indent=2), flush=True)
    target = Path("data/diagnostics/cfpb_access.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
