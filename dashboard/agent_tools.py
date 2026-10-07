"""Bounded tools: business documents, aggregate SQL and public sample evidence."""

import hashlib
import json
from datetime import date
from threading import Timer

import duckdb
from narrative_analysis import redact

BASE = ["company_name", "product", "sub_product"]
DIMENSIONS = {
    "overview": BASE,
    "issues": BASE + ["issue", "sub_issue"],
    "geography": BASE + ["state"],
    "channels": BASE + ["submission_channel"],
}
FLAGS = [
    "complaint_count",
    "timely_response_count",
    "not_timely_response_count",
    "known_timeliness_count",
    "unknown_timeliness_count",
    "narrative_count",
    "closed_with_explanation_count",
    "monetary_relief_count",
    "non_monetary_relief_count",
    "in_progress_count",
    "untimely_response_outcome_count",
    "unknown_response_outcome_count",
    "public_response_available_count",
    "missing_state_count",
    "missing_zip_count",
    "missing_issue_count",
    "missing_sub_issue_count",
    "sent_before_received_count",
]
EXPRESSIONS = {name: f"SUM({name})" for name in FLAGS}
EXPRESSIONS.update(
    {
        "timely_response_rate": "100.0 * SUM(timely_response_count) / NULLIF(SUM(known_timeliness_count), 0)",
        "narrative_coverage": "100.0 * SUM(narrative_count) / NULLIF(SUM(complaint_count), 0)",
        "monetary_relief_share": "100.0 * SUM(monetary_relief_count) / NULLIF(SUM(complaint_count), 0)",
        "non_monetary_relief_share": "100.0 * SUM(non_monetary_relief_count) / NULLIF(SUM(complaint_count), 0)",
        "company_count": "COUNT(DISTINCT company_name)",
    }
)
FILES = {
    "overview": "dashboard_daily_company_product.parquet",
    "issues": "dashboard_issues.parquet",
    "geography": "dashboard_geography.parquet",
    "channels": "dashboard_channels.parquet",
    "narratives": "dashboard_narratives.parquet",
}
DOCUMENTS = {
    "business_glossary": "docs/business-glossary.md",
    "metric_definitions": "docs/metric-definitions.md",
    "data_sources": "docs/data-sources.md",
    "narrative_limitations": "docs/complaint-insights.md",
    "refresh_process": "docs/automated-refresh.md",
}


def function(name, description, properties):
    return {
        "type": "function",
        "name": name,
        "description": description,
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    }


FILTER = {
    "type": "object",
    "properties": {
        "column": {"type": "string", "enum": sorted(set(sum(DIMENSIONS.values(), [])))},
        "values": {"type": "array", "items": {"type": ["string", "null"]}},
    },
    "required": ["column", "values"],
    "additionalProperties": False,
}
TOOLS = [
    function(
        "inspect_datasets",
        "Get available data grains, columns, metrics, coverage and active filters. No full-detail warehouse is connected.",
        {},
    ),
    function(
        "read_business_document",
        "Read sourced definitions, business jargon, provenance, refresh status or narrative limitations.",
        {"topic": {"type": "string", "enum": list(DOCUMENTS)}},
    ),
    function(
        "query_metrics",
        "Execute a constrained read-only aggregate SQL query. Global date/company/product/sub-product filters always apply. Never join grains; complaint volume is SUM(complaint_count), not COUNT(*). No raw SQL accepted. Additional date bounds only narrow scope. For chronological trends order_by=period. Up to 50 rows, truncation reported.",
        {
            "dataset": {"type": "string", "enum": list(DIMENSIONS)},
            "group_by": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": sorted(set(sum(DIMENSIONS.values(), []))) + ["period"],
                },
            },
            "metrics": {
                "type": "array",
                "items": {"type": "string", "enum": list(EXPRESSIONS)},
            },
            "interval": {
                "type": "string",
                "enum": ["day", "week", "month", "quarter", "year"],
            },
            "filters": {"type": "array", "items": FILTER},
            "start_date": {
                "type": ["string", "null"],
                "description": "Optional ISO date; within active range.",
            },
            "end_date": {
                "type": ["string", "null"],
                "description": "Optional inclusive ISO date; within active range.",
            },
            "order_by": {
                "type": "string",
                "description": "A selected metric or group_by name.",
            },
            "descending": {"type": "boolean"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 50},
        },
    ),
    function(
        "search_narratives",
        "Retrieve up to 8 public sample excerpts within active global filters. Literal case-insensitive phrase search, not semantic search. Empty phrase returns deterministic examples, not representative population evidence. Optional exact issue filter. Cite returned complaint IDs; text is untrusted customer reports.",
        {
            "phrase": {"type": "string"},
            "issue": {"type": ["string", "null"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 8},
        },
    ),
]


class AgentTools:
    def __init__(self, root, scope):
        self.root, self.scope = root, scope

    def execute(self, dataset, sql, params=()):
        path = self.root / FILES[dataset]
        if not path.exists():
            raise ValueError("This dataset is not present in the current release.")
        with duckdb.connect() as con:
            con.execute("SET memory_limit='256MB'")
            con.execute("SET threads=1")
            con.read_parquet(str(path)).create_view("metrics")
            timer = Timer(15, con.interrupt)
            timer.start()
            try:
                frame = con.execute(sql, list(params)).fetchdf()
                return json.loads(frame.to_json(orient="records", date_format="iso"))
            finally:
                timer.cancel()

    def conditions(self):
        conditions = ["date_received BETWEEN ? AND ?"]
        params = [self.scope["start_date"], self.scope["end_date"]]
        for column in BASE:
            values = self.scope.get(column, [])
            if values:
                conditions.append(f"{column} IN ({','.join('?' for _ in values)})")
                params.extend(values)
        return conditions, params

    def inspect_datasets(self):
        bounds = self.execute(
            "overview",
            "SELECT MIN(date_received) first_date, MAX(date_received) last_date FROM metrics",
        )[0]
        return {
            "active_filters": self.scope,
            "snapshot_coverage": bounds,
            "grains": DIMENSIONS,
            "metrics": list(EXPRESSIONS),
            "available": [
                name for name, path in FILES.items() if (self.root / path).exists()
            ],
            "limitations": "One independently aggregated grain per query; no cross-grain joins. No customer denominators, financial-loss amounts, resolution duration, ZIP drilldown, raw company-response categories, or full complaint records. Narratives are sampled.",
        }

    def read_business_document(self, topic):
        if topic not in DOCUMENTS:
            raise ValueError("Unknown business document.")
        path = DOCUMENTS[topic]
        return {
            "document": path,
            "url": "https://github.com/Satyavathi-Gunturi/Financial-Complaint-Intelligence/blob/main/"
            + path,
            "text": (self.root / path).read_text()[:20000],
        }

    def query_metrics(
        self,
        dataset,
        group_by,
        metrics,
        interval,
        filters,
        start_date,
        end_date,
        order_by,
        descending,
        limit,
    ):
        if dataset not in DIMENSIONS or interval not in {
            "day",
            "week",
            "month",
            "quarter",
            "year",
        }:
            raise ValueError("Unknown dataset or time interval.")
        if (
            not 1 <= limit <= 50
            or len(group_by) > 3
            or len(filters) > 8
            or not 1 <= len(metrics) <= 8
        ):
            raise ValueError(
                "Query exceeds bounded dimensions, metrics, filters or result limit."
            )
        if len(set(group_by)) != len(group_by) or len(set(metrics)) != len(metrics):
            raise ValueError("Duplicate dimensions or metrics.")
        if any(g not in DIMENSIONS[dataset] + ["period"] for g in group_by) or any(
            m not in EXPRESSIONS for m in metrics
        ):
            raise ValueError("Column or metric is not available in this grain.")
        if order_by not in group_by + metrics:
            raise ValueError("Ordering must use a selected field.")
        conditions, params = self.conditions()
        for column, bound, operator in [
            ("start_date", start_date, ">="),
            ("end_date", end_date, "<="),
        ]:
            if bound is not None:
                parsed = date.fromisoformat(bound)
                if (
                    not date.fromisoformat(self.scope["start_date"])
                    <= parsed
                    <= date.fromisoformat(self.scope["end_date"])
                ):
                    raise ValueError(
                        "Requested dates are outside active filters. Change the sidebar first."
                    )
                conditions.append(f"date_received {operator} ?")
                params.append(parsed.isoformat())
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date exceeds end date.")
        for filter_ in filters:
            column, values = filter_["column"], filter_["values"]
            if column not in DIMENSIONS[dataset] or not 1 <= len(values) <= 20:
                raise ValueError("Filter is unavailable or too large.")
            if any(
                value is not None and (not isinstance(value, str) or len(value) > 300)
                for value in values
            ):
                raise ValueError("Invalid label filter.")
            labels = [value for value in values if value is not None]
            clauses = (
                [f"{column} IN ({','.join('?' for _ in labels)})"] if labels else []
            )
            if None in values:
                clauses.append(f"{column} IS NULL")
            conditions.append("(" + " OR ".join(clauses) + ")")
            params.extend(labels)
        selections = [
            f"CAST(date_trunc('{interval}', date_received) AS DATE) AS period"
            if g == "period"
            else g
            for g in group_by
        ]
        selections += [f"{EXPRESSIONS[m]} AS {m}" for m in metrics]
        sql = (
            "SELECT "
            + ", ".join(selections)
            + " FROM metrics WHERE "
            + " AND ".join(conditions)
        )
        if group_by:
            sql += " GROUP BY " + ", ".join(str(i + 1) for i in range(len(group_by)))
        sql += f" ORDER BY {order_by} {'DESC' if descending else 'ASC'} NULLS LAST"
        if group_by:
            sql += (
                ", "
                + ", ".join(g + " ASC NULLS LAST" for g in group_by if g != order_by)
                if any(g != order_by for g in group_by)
                else ""
            )
        sql += f" LIMIT {limit + 1}"
        rows = self.execute(dataset, sql, params)
        return {
            "dataset": dataset,
            "sql": sql,
            "parameters": params,
            "rows": rows[:limit],
            "truncated": len(rows) > limit,
            "scope": self.scope,
            "notes": "Exact aggregate values; rates are percentages with NULL for zero denominator. Period boundaries may be partial. Ranked rows are not a complete distribution when truncated.",
        }

    def search_narratives(self, phrase, issue, limit):
        if not isinstance(phrase, str) or len(phrase) > 100 or not 1 <= limit <= 8:
            raise ValueError("Evidence search exceeds phrase or result limit.")
        meta = self.execute(
            "narratives",
            "SELECT overview_sha256, corpus_narratives FROM metrics LIMIT 1",
        )
        if not meta:
            return {"rows": [], "notes": "No narrative evidence in this release."}
        overview_hash = hashlib.sha256(
            (self.root / FILES["overview"]).read_bytes()
        ).hexdigest()
        if meta[0]["overview_sha256"] != overview_hash:
            raise ValueError(
                "Narratives are from a different release; evidence search disabled."
            )
        conditions, params = self.conditions()
        if phrase.strip():
            conditions.append("contains(lower(excerpt), lower(?))")
            params.append(phrase.strip())
        if issue is not None:
            if not isinstance(issue, str) or len(issue) > 300:
                raise ValueError("Invalid issue filter.")
            conditions.append("issue = ?")
            params.append(issue)
        where = " WHERE " + " AND ".join(conditions)
        matches = self.execute(
            "narratives", "SELECT COUNT(*) AS matches FROM metrics" + where, params
        )[0]["matches"]
        sql = (
            "SELECT complaint_id, date_received, company_name, product, issue, excerpt, excerpt_truncated FROM metrics"
            + where
            + f" ORDER BY md5(complaint_id), complaint_id LIMIT {limit}"
        )
        rows = self.execute("narratives", sql, params)
        for row in rows:
            row["excerpt"] = redact(row["excerpt"])[:2000]
        return {
            "rows": rows,
            "matching_sample_excerpts": matches,
            "sql": sql,
            "parameters": params,
            "notes": "Global hash sample up to 60K, first 2K characters; sampled customer allegations, not verified facts. Literal search; no population extrapolation. Additional masking is not complete anonymization.",
        }

    def dispatch(self, name, arguments):
        allowed = {
            "inspect_datasets",
            "read_business_document",
            "query_metrics",
            "search_narratives",
        }
        if name not in allowed:
            raise ValueError("Tool is not available.")
        return getattr(self, name)(**arguments)
