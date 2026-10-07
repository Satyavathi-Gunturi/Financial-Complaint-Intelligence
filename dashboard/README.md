# Complaint analytics dashboard

> **Refresh enabled; updates may fail (2026-10-05):** CFPB HTTP 403 errors may prevent downloads. Scheduled runs remain active; failed attempts preserve the last validated snapshot. See [refresh operation](../docs/automated-refresh.md).

Run from the repository root:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The deployed app queries four root-level Parquet snapshots independently using DuckDB: company/product, issues, geography and channels. The export has 873,137 daily company/product rows representing 14,482,997 complaints; all 18 additive metric totals were reconciled in Colab. Filters include received date, company, product and sub-product. Rates use summed flags and their documented denominators. No full database or credentials are required.

Deploy on Streamlit Community Cloud with the repository, `main` branch and entry point `dashboard/app.py`. Use Python 3.12. The requirements beside the entry point isolate serving dependencies from dbt. Hosting resource limits still apply; compressed file size is not memory usage. This is a snapshot dashboard, not a live feed or deployed AI agent.

The dashboard displays raw complaint volumes without company customer-count normalization. First/last trend periods can be partial; missing labels remain included when their filter is empty. Other response outcomes are calculated as the remainder after displayed mutually exclusive outcome flags. Full complaint records and full narrative text remain in the separate database checkpoint; a fifth Parquet supplies sampled excerpts to Complaint Insights; aggregate issue, geography and channel metrics are available in the dashboard tabs.

Validation: `python dashboard/check_app.py` checks real-snapshot headline totals and exercises product, date and weekly trend filters with Streamlit AppTest.

## Refresh status
The daily rolling-refresh implementation is in place, but its first GitHub-hosted archive download returned HTTP 403 on 2026-10-05. No rolling release has been published; current serving data still spans November 2022–August 2026. See [refresh operations](../docs/automated-refresh.md).

## Seven-tab executive dashboard
Overview, Trends, Companies, Products & Issues, Response Outcomes, Geography & Channels, and Complaint Insights share date/company/product/sub-product filters. Root-level issue, geography and channel Parquet exports supply separate reconciled grains; they are queried individually and never joined together. Issue drilldown is local to the issue charts. Previous-period change is available only when the entire equal-length window is within snapshot coverage. State maps exclude unmappable labels but preserve their counts in the accompanying table. Display counts use K/M/B; downloads preserve exact values. Complaint Insights provides local NLP topic discovery and literal evidence search. Semantic retrieval and an LLM agent remain planned. See [analysis contracts and limitations](../docs/complaint-insights.md).

Complaint Insights presents an executive briefing and ranked source-issue concern cards instead of a word-cluster chart. Each card includes sample support and a verbatim excerpt/complaint ID; investigation questions and detailed evidence sit below. Styled word clusters show phrase mention counts and filter evidence; detailed NLP methodology is expandable.
