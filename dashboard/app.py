"""Explore the validated CFPB daily company/product complaint snapshot."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "dashboard_daily_company_product.parquet"
st.set_page_config(
    page_title="Financial Complaint Intelligence", page_icon="📊", layout="wide"
)


@st.cache_data(show_spinner=False)
def query(sql, params=()):
    """Run parameterized analytics on the packaged Parquet snapshot."""
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.read_parquet(str(DATA)).create_view("metrics")
        return con.execute(sql, list(params)).fetchdf()


def rate(numerator, denominator):
    """Preserve unknown rates when no eligible denominator exists."""
    return f"{100 * numerator / denominator:.2f}%" if denominator else "N/A"


st.title("Financial Complaint Intelligence")
st.caption("CFPB complaint snapshot · Received November 2022–August 2026")
st.info(
    "Explore reported complaint patterns and recorded responses. Volumes are not adjusted for company size or customer count and do not establish root causes."
)
if not DATA.exists():
    st.error(
        "Dashboard dataset is missing. Add dashboard_daily_company_product.parquet at the repository root."
    )
    st.stop()

bounds = query(
    "SELECT MIN(date_received) AS first, MAX(date_received) AS last FROM metrics"
).iloc[0]
with st.sidebar:
    st.header("Explore the snapshot")
    dates = st.date_input(
        "Received date range",
        value=(bounds["first"].date(), bounds["last"].date()),
        min_value=bounds["first"].date(),
        max_value=bounds["last"].date(),
    )
    companies = st.multiselect(
        "Companies",
        query(
            "SELECT DISTINCT company_name FROM metrics WHERE company_name IS NOT NULL ORDER BY 1"
        )["company_name"].tolist(),
    )
    products = st.multiselect(
        "Products",
        query(
            "SELECT DISTINCT product FROM metrics WHERE product IS NOT NULL ORDER BY 1"
        )["product"].tolist(),
    )
    product_where = (
        " WHERE product IN (" + ",".join("?" for _ in products) + ")"
        if products
        else ""
    )
    subs = st.multiselect(
        "Sub-products",
        query(
            "SELECT DISTINCT sub_product FROM metrics"
            + product_where
            + (" AND" if products else " WHERE")
            + " sub_product IS NOT NULL ORDER BY 1",
            tuple(products),
        )["sub_product"].tolist(),
    )
    grain = st.selectbox("Trend interval", ["Month", "Week", "Day"])
    st.caption(
        "Empty selections include all values, including missing labels. Dates use the complaint received date; weeks start Monday."
    )

if len(dates) != 2:
    st.warning("Select both a start and end date.")
    st.stop()
conditions = ["date_received BETWEEN ? AND ?"]
params = list(dates)
for column, values in [
    ("company_name", companies),
    ("product", products),
    ("sub_product", subs),
]:
    if values:
        conditions.append(f"{column} IN ({','.join('?' for _ in values)})")
        params.extend(values)
where = " WHERE " + " AND ".join(conditions)
params = tuple(params)
totals = (
    query(
        "SELECT SUM(complaint_count) AS complaints, SUM(timely_response_count) AS timely, SUM(known_timeliness_count) AS known, SUM(narrative_count) AS narratives, SUM(unknown_timeliness_count) AS unknown FROM metrics"
        + where,
        params,
    )
    .iloc[0]
    .fillna(0)
)
if not totals["complaints"]:
    st.warning("No complaints match these filters. Adjust the selections.")
    st.stop()

cards = st.columns(4)
cards[0].metric("Complaints", f"{int(totals['complaints']):,}")
cards[1].metric("Timely response rate", rate(totals["timely"], totals["known"]))
cards[2].metric("Narrative coverage", rate(totals["narratives"], totals["complaints"]))
cards[3].metric("Published narratives", f"{int(totals['narratives']):,}")
st.caption(
    f"Timeliness denominator: {int(totals['known']):,} known records · Unknown timeliness: {int(totals['unknown']):,}. Rates are calculated after aggregation."
)

trend = query(
    f"SELECT CAST(date_trunc('{grain.lower()}', date_received) AS DATE) AS period, SUM(complaint_count) AS complaints, SUM(narrative_count) AS narratives FROM metrics"
    + where
    + " GROUP BY 1 ORDER BY 1",
    params,
)
st.subheader("Complaint volume over time")
st.plotly_chart(
    px.line(
        trend,
        x="period",
        y="complaints",
        markers=True,
        labels={"period": "Received period", "complaints": "Complaints"},
    ),
    width="stretch",
)
st.caption(
    "First and last buckets may cover partial periods. A missing bucket has no matching complaints; published narratives are available only for a subset of records."
)

left, right = st.columns(2)
for column, label, container in [
    ("company_name", "Companies", left),
    ("product", "Products", right),
]:
    ranked = query(
        f"SELECT COALESCE({column}, 'Missing label') AS category, SUM(complaint_count) AS complaints FROM metrics"
        + where
        + " GROUP BY 1 ORDER BY complaints DESC, category LIMIT 15",
        params,
    )
    with container:
        st.subheader(f"Top {label.lower()} by volume")
        st.plotly_chart(
            px.bar(
                ranked.sort_values("complaints"),
                x="complaints",
                y="category",
                orientation="h",
                labels={"category": label, "complaints": "Complaints"},
            ),
            width="stretch",
        )

outcomes = query(
    "SELECT SUM(closed_with_explanation_count) AS explanation, SUM(monetary_relief_count) AS monetary, SUM(non_monetary_relief_count) AS non_monetary, SUM(in_progress_count) AS in_progress, SUM(untimely_response_outcome_count) AS untimely, SUM(unknown_response_outcome_count) AS missing FROM metrics"
    + where,
    params,
).iloc[0]
outcome_rows = [
    ("Closed with explanation", outcomes["explanation"]),
    ("Monetary relief", outcomes["monetary"]),
    ("Non-monetary relief", outcomes["non_monetary"]),
    ("In progress", outcomes["in_progress"]),
    ("Untimely response outcome", outcomes["untimely"]),
    ("Missing outcome", outcomes["missing"]),
]
outcome_rows.append(
    (
        "Other recorded outcomes",
        max(0, totals["complaints"] - sum(v for _, v in outcome_rows)),
    )
)
outcome_frame = pd.DataFrame(outcome_rows, columns=["Recorded outcome", "Complaints"])
st.subheader("Recorded company response outcomes")
st.plotly_chart(
    px.bar(outcome_frame, x="Recorded outcome", y="Complaints"),
    width="stretch",
)
st.caption(
    "Outcome categories reflect the export snapshot. They do not measure customer satisfaction, relief amounts, or current resolution status."
)
with st.expander("Trend data and definitions"):
    st.dataframe(trend, hide_index=True, width="stretch")
    st.download_button(
        "Download filtered trend CSV",
        trend.to_csv(index=False),
        "complaint_trend.csv",
        "text/csv",
    )
    st.markdown(
        "**Timely response rate:** timely response count ÷ known timeliness count. **Narrative coverage:** published narrative count ÷ complaint count. This aggregate supports date, company and product exploration. Issue, state, individual narrative retrieval and AI chat are not included in this dashboard."
    )
