"""Explore the validated CFPB daily company/product complaint snapshot."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "dashboard_daily_company_product.parquet"
st.set_page_config(
    page_title="Financial Complaint Intelligence", page_icon="◈", layout="wide"
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


st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {background: #f3f5f8;}
[data-testid="stHeader"] {background: rgba(243,245,248,.96);}
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1550px;}
[data-testid="stSidebar"] {background: #e9eef4; border-right: 1px solid #d7e0e9;}
h1,h2,h3 {color: #10243a; letter-spacing: -.035em;}
h3 {font-size: 1.2rem !important; margin-top: .8rem;}
[data-testid="stMetric"] {background: #fff; border: 1px solid #e0e6ee; border-top: 3px solid #147d83; border-radius: 14px; padding: 20px 18px; box-shadow: 0 4px 16px rgba(20,38,62,.035);}
[data-testid="stMetricLabel"] {color: #52657a; font-size: .83rem;}
[data-testid="stMetricValue"] {color: #10243a; font-weight: 650; font-size: clamp(1.35rem,2.1vw,2.3rem); letter-spacing: -.045em;}
[data-testid="stPlotlyChart"] {background: white; border: 1px solid #e0e6ee; border-radius: 14px; overflow: hidden; padding: 5px;}
[data-testid="stExpander"] {background: #fff; border: 1px solid #e0e6ee; border-radius: 12px;}
.hero {background: linear-gradient(115deg,#0d2137 0%,#153951 70%,#17565c 100%); border-radius: 18px; padding: 30px 34px; margin-bottom: 22px; color: #fff;}
.hero .eyebrow {color: #8de0d2; font-size: .7rem; letter-spacing: .18em; font-weight: 700; margin-bottom: 13px;}
.hero h1 {color: #fff; font-size: clamp(1.7rem,3vw,2.6rem); line-height: 1.12; padding: 0; margin: 0 0 12px; letter-spacing: -.045em;}
.hero p {color: #c0d2df; font-size: .94rem; margin: 0 0 20px; max-width: 750px;}
.badge {display: inline-block; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.16); border-radius: 30px; padding: 5px 12px; margin: 0 6px 4px 0; font-size: .72rem; color: #d6e6ef;}
.scope {color: #52657a; font-size: .8rem; margin: 4px 0 18px;}
.brief {background: #e5f1ef; border-left: 3px solid #147d83; padding: 14px 18px; border-radius: 0 10px 10px 0; color: #254d50; margin: 12px 0 20px; font-size: .88rem;}
.footer {border-top: 1px solid #dbe2eb; color: #64748b; font-size: .75rem; padding-top: 16px; margin-top: 28px;}
@media(max-width: 700px) {.hero {padding: 22px;} .block-container {padding-top: 1.3rem;} [data-testid="stMetric"] {padding: 14px;}}
</style>
<div class="hero">
<div class="eyebrow">FINANCIAL COMPLAINT INTELLIGENCE / EXECUTIVE OVERVIEW</div>
<h1>A clearer view of customer complaints.</h1>
<p>Explore complaint demand, recorded company responses and the availability of customer narrative evidence.</p>
<span class="badge">CFPB public complaint data</span>
<span class="badge">Nov 2022 – Aug 2026</span>
<span class="badge">Validated snapshot</span>
</div>
""",
    unsafe_allow_html=True,
)


def style_chart(fig, height=340):
    """Apply a consistent, readable executive chart theme."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", color="#52657a", size=12),
        margin=dict(l=20, r=24, t=30, b=35),
        colorway=["#147d83", "#294e73", "#63ada7", "#b99154", "#95a6b8"],
        hoverlabel=dict(bgcolor="#10243a", font_color="white"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#edf1f5", zeroline=False)
    return fig


if not DATA.exists():
    st.error(
        "Dashboard dataset is missing. Add dashboard_daily_company_product.parquet at the repository root."
    )
    st.stop()

bounds = query(
    "SELECT MIN(date_received) AS first, MAX(date_received) AS last FROM metrics"
).iloc[0]
with st.sidebar:
    st.markdown("### ◈ Intelligence workspace")
    st.caption("Configure the executive view")
    st.divider()
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

st.markdown(
    f'<div class="scope">SELECTED VIEW · {dates[0]:%d %b %Y} — {dates[1]:%d %b %Y} · {len(companies) if companies else "All"} companies · {len(products) if products else "All"} products</div>',
    unsafe_allow_html=True,
)
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
st.subheader("01 / Complaint demand")
st.plotly_chart(
    style_chart(
        px.area(
            trend,
            x="period",
            y="complaints",
            markers=True,
            labels={"period": "Received period", "complaints": "Complaints"},
            color_discrete_sequence=["#147d83"],
        )
    ).update_traces(line_width=2.5, fillcolor="rgba(20,125,131,.09)", marker_size=5),
    width="stretch",
)
st.caption(
    "First and last buckets may cover partial periods. A missing bucket has no matching complaints; published narratives are available only for a subset of records."
)

st.subheader("02 / Where complaints concentrate")
left, right = st.columns(2)
for column, label, container in [
    ("company_name", "Companies", left),
    ("product", "Products", right),
]:
    ranked = query(
        f"SELECT COALESCE({column}, 'Missing label') AS category, SUM(complaint_count) AS complaints FROM metrics"
        + where
        + " GROUP BY 1 ORDER BY complaints DESC, category LIMIT 10",
        params,
    )
    with container:
        st.markdown(f"**Top 10 {label.lower()}**")
        st.plotly_chart(
            style_chart(
                px.bar(
                    ranked.sort_values("complaints").assign(
                        display_label=lambda frame: frame["category"].map(
                            lambda label: label if len(label) < 36 else label[:33] + "…"
                        )
                    ),
                    x="complaints",
                    y="display_label",
                    orientation="h",
                    labels={"display_label": "", "complaints": "Complaints"},
                    hover_name="category",
                    color_discrete_sequence=["#294e73"],
                ),
                height=400,
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
st.subheader("03 / Recorded response outcomes")
st.plotly_chart(
    style_chart(
        px.bar(
            outcome_frame.sort_values("Complaints"),
            x="Complaints",
            y="Recorded outcome",
            orientation="h",
            color_discrete_sequence=["#147d83"],
            labels={"Recorded outcome": ""},
        ),
        height=340,
    ),
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

st.markdown(
    '<div class="footer">Financial Complaint Intelligence · Source: CFPB public complaint snapshot. Raw volumes are not normalized by company size or customer count and do not establish internal root causes.</div>',
    unsafe_allow_html=True,
)
