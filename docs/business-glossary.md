# Business context and glossary

Financial Complaint Intelligence helps financial-services leadership inspect complaint demand, recorded company responses, data coverage and customer-reported experiences. It supports investigation prioritization; it does not establish misconduct, internal root cause or company risk scores.

## Business language

| Term / keyword | Meaning and interpretation |
|---|---|
| CFPB | Consumer Financial Protection Bureau, the source of the public Consumer Complaint Database. The source is external to this project. |
| Complaint volume / demand | Published complaint records in the selected received-date range. Use SUM(complaint_count), not the number of aggregate rows. |
| Received date | When CFPB received the complaint; default reporting date. It differs from the date sent to the company. |
| Company | Recorded company name. Complaint totals are not normalized by customers, market share or company size. |
| Product / sub-product | CFPB's recorded financial-product classification. Product labels can differ over time. |
| Issue / sub-issue | Recorded complaint category. This is not an AI-verified diagnosis. An issue grain supports issue drilldown; another grain may not. |
| Timely response | Source Yes/No timeliness flag. Timely response rate uses records with known timeliness as its denominator. It does not measure satisfaction, quality or resolution time. |
| Untimely response outcome | A recorded outcome category, distinct from the timeliness flag. These must not be substituted. |
| Closed with explanation | A recorded company response classification; it does not mean the customer accepted the explanation. |
| Monetary relief | A response category indicating monetary relief. Dollar amounts and financial-loss estimates are not available. |
| Non-monetary relief | A response category indicating non-monetary relief; do not infer its value or customer satisfaction. |
| In progress | Status in the snapshot, not a live pending-case queue. |
| Public response available | A public response category is recorded. This is not free-text company response content. |
| Narrative / complaint description | Customer-provided public text. Availability is uneven; reported events and allegations are not independently verified. |
| Narrative coverage | Published narratives divided by complaints. Missing public text is not absence of a problem. |
| Share / percentage points (pp) | Share requires a stated denominator. A change from 20% to 25% is +5 pp, not +5%. |
| Trend / prior period | Received-date counts by day, Monday-start week, month, quarter or year. Partial buckets and unequal windows must be disclosed. |
| State / geography | Recorded state, not necessarily incident location. Counts are not population-adjusted. ZIP drilldown is not in the serving files. |
| Submission channel | Recorded route used to submit the complaint, such as Web or Phone. |
| K / M / B | Thousand / million / billion. Display values are rounded; query result tables preserve exact numbers. |
| Snapshot | A validated static publication, not a live feed. Actual dates must come from dataset inspection. |
| Rolling retention | Automated release aims to retain the latest 36 calendar months. Source HTTP 403 failures can prevent refresh while the previous validated snapshot remains served. |
| Bronze / silver / gold | Raw retained inputs / relational cleaned data / analytical wide and star models. These batch layers are not directly connected to the deployed chatbot. |
| dbt / DuckDB / Parquet | Tested SQL transformations / analytical query engine / packaged columnar serving files. |
| NLP / word cluster | TF–IDF/NMF groups recurring language in sampled excerpts. Cluster labels and weights do not establish sentiment, confidence or causal factors. |

## Decision and data rules

Use independently reconciled overview, issue, state and channel aggregate exports for full complaint metrics. Do not join these grains together: a many-to-many join would double count. Each query supports company/product/sub-product and received dates, plus the chosen grain's own dimensions. Questions combining issue and state are not supported by the current serving exports.

Use the narrative export only for sampled evidence and sample counts, never to infer full complaint counts. Literal phrase retrieval is not semantic search. Complaint IDs identify the returned records; other personal details may remain despite limited masking.

Global sidebar filters define the chatbot scope. Additional tool filters may narrow it; the agent cannot silently expand it. Local chart drilldowns are not global chatbot filters. Numerical facts require executed query results; business definitions and source facts require cited repository documents.

Source references: [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/), [metric definitions](metric-definitions.md), [source inventory](data-sources.md) and [narrative contract](complaint-insights.md).
