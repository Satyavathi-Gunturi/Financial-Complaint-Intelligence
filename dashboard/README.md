# Complaint analytics dashboard

Run from the repository root:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The app queries the root `dashboard_daily_company_product.parquet` snapshot using DuckDB. The export has 873,137 daily company/product rows representing 14,482,997 complaints; all 18 additive metric totals were reconciled in Colab. Filters include received date, company, product and sub-product. Rates use summed flags and their documented denominators. No full database or credentials are required.

Deploy on Streamlit Community Cloud with the repository, `main` branch and entry point `dashboard/app.py`. Use Python 3.12. The requirements beside the entry point isolate serving dependencies from dbt. Hosting resource limits still apply; compressed file size is not memory usage. This is a snapshot dashboard, not a live feed or deployed AI agent.

The dashboard displays raw complaint volumes without company customer-count normalization. First/last trend periods can be partial; missing labels remain included when their filter is empty. Other response outcomes are calculated as the remainder after displayed mutually exclusive outcome flags. Full complaint records, issues, geography and narrative text remain in the separate database checkpoint.

Validation: `python dashboard/check_app.py` checks real-snapshot headline totals and exercises product, date and weekly trend filters with Streamlit AppTest.

## Six-tab executive dashboard
Overview, Trends, Companies, Products & Issues, Response Outcomes, and Geography & Channels share date/company/product/sub-product filters. Root-level issue, geography and channel Parquet exports supply separate reconciled grains; they are queried individually and never joined together. Issue drilldown is local to the issue charts. Previous-period change is available only when the entire equal-length window is within snapshot coverage. State maps exclude unmappable labels but preserve their counts in the accompanying table. Display counts use K/M/B; downloads preserve exact values. AI narrative search and an LLM agent are not yet implemented.
