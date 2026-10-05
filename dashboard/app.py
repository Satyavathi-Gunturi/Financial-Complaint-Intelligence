"""Explore the validated CFPB daily company/product complaint snapshot."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dashboard_daily_company_product.parquet"
DATASETS = {
    "overview": DATA,
    "issues": ROOT / "dashboard_issues.parquet",
    "geography": ROOT / "dashboard_geography.parquet",
    "channels": ROOT / "dashboard_channels.parquet",
}
st.set_page_config(
    page_title="Financial Complaint Intelligence", page_icon="◈", layout="wide"
)


@st.cache_data(show_spinner=False)
def query(sql, params=(), dataset="overview"):
    """Run parameterized analytics on the packaged Parquet snapshot."""
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.read_parquet(str(DATASETS[dataset])).create_view("metrics")
        return con.execute(sql, list(params)).fetchdf()


def rate(numerator, denominator):
    """Preserve unknown rates when no eligible denominator exists."""
    return f"{100 * numerator / denominator:.2f}%" if denominator else "N/A"


def compact(value):
    """Format counts using consistent leadership-facing K/M/B notation."""
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    if abs(value) >= 1_000:
        rounded = round(value / 1_000)
        if rounded >= 1000:
            return f"{value / 1_000_000:.2f} M"
        return f"{rounded:.0f}K"
    return f"{value:.0f}"


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
<div class="eyebrow">FINANCIAL COMPLAINT INTELLIGENCE</div>
<h1>The Consumer Complaint Landscape</h1>
<p>Explore where complaints concentrate and how companies respond.</p>
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
cards[0].metric("Complaints", compact(totals["complaints"]))
cards[1].metric("Timely response rate", rate(totals["timely"], totals["known"]))
cards[2].metric("Narrative coverage", rate(totals["narratives"], totals["complaints"]))
cards[3].metric("Published narratives", compact(totals["narratives"]))
st.caption(
    f"Timeliness denominator: {compact(totals['known'])} known records · Unknown timeliness: {compact(totals['unknown'])}. Rates are calculated after aggregation."
)


def count_chart(frame, category, title, color="#294e73", height=400):
    """Render ranked values with compact labels and full category tooltips."""
    frame = frame.copy().sort_values("complaints")
    frame["label"] = frame[category].fillna("Missing label").map(str)
    frame["short"] = frame["label"].map(lambda v: v if len(v) < 40 else v[:37] + "…")
    frame["count_label"] = frame["complaints"].map(compact)
    fig = style_chart(
        px.bar(
            frame,
            x="complaints",
            y="short",
            orientation="h",
            text="count_label",
            custom_data=["label", "count_label"],
            labels={"short": "", "complaints": "Complaints"},
            color_discrete_sequence=[color],
        ),
        height,
    )
    fig.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{customdata[0]}</b><br>Complaints: %{customdata[1]}<extra></extra>",
    )
    maximum = frame["complaints"].max()
    ticks = [maximum * i / 4 for i in range(5)]
    fig.update_xaxes(tickvals=ticks, ticktext=[compact(v) for v in ticks])
    fig.update_layout(margin=dict(l=20, r=80, t=25, b=35))
    st.markdown(f"**{title}**")
    st.plotly_chart(fig, width="stretch", key=title)


def display_table(frame, counts=()):
    """Keep on-screen counts compact; exports retain exact values."""
    display = frame.copy()
    for col in counts:
        display[col] = display[col].map(compact)
    st.dataframe(display, hide_index=True, width="stretch")


def rank(column, dataset="overview", extra="", extra_params=(), limit=10):
    return query(
        f"SELECT COALESCE({column}, 'Missing label') AS category, "
        "SUM(complaint_count) AS complaints FROM metrics"
        + where
        + extra
        + f" GROUP BY 1 ORDER BY complaints DESC, category LIMIT {limit}",
        params + tuple(extra_params),
        dataset,
    )


def trend_chart(frame, key):
    frame = frame.copy()
    frame["count_label"] = frame["complaints"].map(compact)
    fig = style_chart(
        px.area(
            frame,
            x="period",
            y="complaints",
            markers=True,
            custom_data=["count_label"],
            color_discrete_sequence=["#147d83"],
            labels={"period": "Received period", "complaints": "Complaints"},
        )
    )
    fig.update_traces(
        line_width=2.5,
        marker_size=5,
        fillcolor="rgba(20,125,131,.09)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Complaints: %{customdata[0]}<extra></extra>",
    )
    maximum = frame["complaints"].max()
    ticks = [maximum * i / 4 for i in range(5)]
    fig.update_yaxes(tickvals=ticks, ticktext=[compact(v) for v in ticks])
    st.plotly_chart(fig, width="stretch", key=key)


trend = query(
    f"SELECT CAST(date_trunc('{grain.lower()}', date_received) AS DATE) AS period, "
    "SUM(complaint_count) AS complaints, SUM(narrative_count) AS narratives "
    "FROM metrics" + where + " GROUP BY 1 ORDER BY 1",
    params,
)

overview, trends, company_tab, issues_tab, response_tab, geo_tab = st.tabs(
    [
        "Overview",
        "Trends",
        "Companies",
        "Products & Issues",
        "Response Outcomes",
        "Geography & Channels",
    ]
)

with overview:
    st.subheader("Complaint demand at a glance")
    trend_chart(trend, "overview_trend")
    st.caption(
        "Received-date counts. First and last buckets may be partial. Public complaint volume is not normalized by company size or customer count."
    )
    left, right = st.columns(2)
    with left:
        count_chart(
            rank("company_name", limit=5),
            "category",
            "Leading companies by volume",
            height=290,
        )
    with right:
        count_chart(
            rank("product", limit=5),
            "category",
            "Leading products by volume",
            "#147d83",
            290,
        )
    top5 = rank("company_name", limit=5)["complaints"].sum()
    st.caption(
        f"Top five companies account for {100 * top5 / totals['complaints']:.2f}% of complaints in the selected view. Concentration is a volume measure, not a company performance rating."
    )

with trends:
    st.subheader("Volume and change over time")
    from datetime import timedelta

    duration = (dates[1] - dates[0]).days + 1
    prior_end = dates[0] - timedelta(days=1)
    prior_start = prior_end - timedelta(days=duration - 1)
    if prior_start >= bounds["first"].date():
        previous = query(
            "SELECT SUM(complaint_count) AS complaints FROM metrics" + where,
            (prior_start, prior_end) + params[2:],
        ).iloc[0]["complaints"]
        previous = 0 if pd.isna(previous) else previous
        c1, c2, c3 = st.columns(3)
        c1.metric("Current period", compact(totals["complaints"]))
        c2.metric("Previous equal-length period", compact(previous))
        c3.metric(
            "Volume change",
            f"{100 * (totals['complaints'] / previous - 1):+.2f}%"
            if previous
            else "N/A",
        )
        st.caption(
            f"Previous comparison window: {prior_start:%d %b %Y}–{prior_end:%d %b %Y}. Same company/product filters; equal number of days."
        )
    else:
        st.caption(
            "Previous-period change is unavailable: the equal-length comparison would extend before snapshot coverage. Select a shorter, later date range to compare."
        )
    trend_chart(trend, "detail_trend")
    st.caption(
        "Trend interval follows the sidebar selection. Missing buckets have no matching complaints; boundary periods can be partial."
    )
    st.markdown("**Published narrative coverage by period**")
    coverage = trend.copy()
    coverage["coverage_pct"] = 100 * coverage["narratives"] / coverage["complaints"]
    coverage["count_label"] = coverage["complaints"].map(compact)
    coverage["narrative_label"] = coverage["narratives"].map(compact)
    fig = style_chart(
        px.line(
            coverage,
            x="period",
            y="coverage_pct",
            markers=True,
            custom_data=["count_label", "narrative_label"],
            color_discrete_sequence=["#b99154"],
            labels={
                "period": "Received period",
                "coverage_pct": "Narrative coverage (%)",
            },
        )
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_traces(
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Coverage: %{y:.2f}%<br>Complaints: %{customdata[0]}<br>Narratives: %{customdata[1]}<extra></extra>"
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Published narrative availability varies over time; absence of text does not mean absence of customer problems."
    )
    with st.expander("Download report data"):
        display_table(trend, ["complaints", "narratives"])
        st.download_button(
            "Download filtered trends",
            trend.to_csv(index=False),
            "complaint_trends.csv",
            "text/csv",
        )

with company_tab:
    st.subheader("Company concentration and recorded responses")
    count_chart(
        rank("company_name", limit=15),
        "category",
        "Top 15 companies by complaint volume",
        height=520,
    )
    company_metrics = query(
        "SELECT COALESCE(company_name, 'Missing label') AS company, "
        "SUM(complaint_count) AS complaints, "
        "100.0 * SUM(timely_response_count) / NULLIF(SUM(known_timeliness_count),0) AS timely_rate_pct, "
        "100.0 * SUM(narrative_count) / NULLIF(SUM(complaint_count),0) AS narrative_coverage_pct "
        "FROM metrics" + where + " GROUP BY 1 ORDER BY complaints DESC, company",
        params,
    )
    company_metrics["complaint_share_pct"] = (
        100 * company_metrics["complaints"] / totals["complaints"]
    )
    shown = company_metrics.copy()
    for col in ["timely_rate_pct", "narrative_coverage_pct", "complaint_share_pct"]:
        shown[col] = shown[col].map(
            lambda value: f"{value:.2f}%" if pd.notna(value) else "N/A"
        )
    display_table(shown, ["complaints"])
    st.download_button(
        "Download company comparison",
        company_metrics.to_csv(index=False),
        "company_comparison.csv",
        "text/csv",
    )
    st.caption(
        "These rates use each company's eligible records. Complaint share is relative to the selected view, not market share."
    )

with issues_tab:
    st.subheader("Products, issues and sub-issues")
    product_totals = rank("product", limit=100)
    product_totals["count_label"] = product_totals["complaints"].map(compact)
    product_totals["share_pct"] = (
        100 * product_totals["complaints"] / totals["complaints"]
    )
    fig = px.treemap(
        product_totals,
        path=["category"],
        values="complaints",
        custom_data=["count_label", "share_pct"],
        color_discrete_sequence=["#294e73", "#147d83", "#63ada7", "#b99154"],
    )
    fig.update_traces(
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Complaints: %{customdata[0]}<br>Share: %{customdata[1]:.2f}%<extra></extra>",
    )
    fig.update_layout(
        height=390,
        margin=dict(l=10, r=10, t=10, b=10),
        uniformtext=dict(minsize=12, mode="hide"),
    )
    st.plotly_chart(fig, width="stretch")
    issue_options = query(
        "SELECT DISTINCT issue FROM metrics"
        + where
        + " AND issue IS NOT NULL ORDER BY 1",
        params,
        "issues",
    )["issue"].tolist()
    chosen_issue = st.selectbox("Drill into an issue", ["All issues"] + issue_options)
    extra = " AND issue = ?" if chosen_issue != "All issues" else ""
    extra_params = (chosen_issue,) if extra else ()
    left, right = st.columns(2)
    with left:
        count_chart(
            rank("issue", "issues", extra, extra_params),
            "category",
            "Leading issues",
            height=430,
        )
    with right:
        count_chart(
            rank("sub_issue", "issues", extra, extra_params),
            "category",
            "Leading sub-issues",
            "#147d83",
            430,
        )
    st.caption(
        "The issue selection applies to these two drilldown charts. Product treemap and headline KPIs retain the global filters. Missing labels are retained; source product labels are not merged."
    )

with response_tab:
    st.subheader("Response timeliness and outcome mix")
    response = (
        query(
            "SELECT SUM(not_timely_response_count) AS not_timely, SUM(unknown_response_outcome_count) AS missing, "
            "SUM(monetary_relief_count) AS monetary, SUM(non_monetary_relief_count) AS non_monetary, "
            "SUM(closed_with_explanation_count) AS explanation, SUM(in_progress_count) AS in_progress, "
            "SUM(untimely_response_outcome_count) AS untimely FROM metrics" + where,
            params,
        )
        .iloc[0]
        .fillna(0)
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Not-timely response rate", rate(response["not_timely"], totals["known"]))
    c2.metric(
        "Recorded relief share",
        rate(response["monetary"] + response["non_monetary"], totals["complaints"]),
    )
    c3.metric("Missing response outcomes", compact(response["missing"]))
    outcome_rows = [
        ("Closed with explanation", response["explanation"]),
        ("Monetary relief", response["monetary"]),
        ("Non-monetary relief", response["non_monetary"]),
        ("In progress", response["in_progress"]),
        ("Untimely response outcome", response["untimely"]),
        ("Missing outcome", response["missing"]),
    ]
    outcome_rows.append(
        (
            "Other outcomes",
            max(0, totals["complaints"] - sum(v for _, v in outcome_rows)),
        )
    )
    outcomes = pd.DataFrame(outcome_rows, columns=["outcome", "complaints"])
    outcomes["count_label"] = outcomes["complaints"].map(compact)
    outcomes["share_pct"] = 100 * outcomes["complaints"] / totals["complaints"]
    left, right = st.columns([1, 1])
    with left:
        fig = px.pie(
            outcomes[outcomes["complaints"] > 0],
            names="outcome",
            values="complaints",
            hole=0.65,
            custom_data=["count_label", "share_pct"],
            color_discrete_sequence=[
                "#294e73",
                "#b99154",
                "#147d83",
                "#63ada7",
                "#95a6b8",
                "#d4dce5",
            ],
        )
        fig.update_traces(
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Complaints: %{customdata[0]}<br>Share: %{customdata[1]:.2f}%<extra></extra>",
        )
        fig.update_layout(
            height=410,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, width="stretch")
    with right:
        shown = outcomes[["outcome", "complaints", "share_pct"]].copy()
        shown["share_pct"] = shown["share_pct"].map(lambda v: f"{v:.2f}%")
        display_table(shown, ["complaints"])
    st.caption(
        "Relief share combines recorded monetary and non-monetary relief; no dollar amounts are available. In-progress status reflects the snapshot, not a live backlog. Recorded outcome categories and source timeliness are different fields."
    )

with geo_tab:
    st.subheader("Geographic and submission-channel patterns")
    states = rank("state", "geography", limit=100)
    states["count_label"] = states["complaints"].map(compact)
    state_codes = set(
        "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
    )
    mapped = states[states["category"].isin(state_codes)]
    fig = px.choropleth(
        mapped,
        locations="category",
        locationmode="USA-states",
        scope="usa",
        color="complaints",
        custom_data=["count_label"],
        color_continuous_scale=["#e3efef", "#147d83", "#10243a"],
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Complaints: %{customdata[0]}<extra></extra>"
    )
    max_count = mapped["complaints"].max() if not mapped.empty else 0
    ticks = [max_count * i / 4 for i in range(5)] if max_count else [0]
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(
            title="Complaints", tickvals=ticks, ticktext=[compact(v) for v in ticks]
        ),
    )
    st.plotly_chart(fig, width="stretch")
    omitted = states[~states["category"].isin(state_codes)]["complaints"].sum()
    st.caption(
        f"Map shows U.S. states and DC. Other or missing locations ({compact(omitted)} complaints) remain in totals and the table below. Counts are not population-adjusted."
    )
    left, right = st.columns(2)
    with left:
        count_chart(
            states.head(10), "category", "Leading recorded locations", height=400
        )
    with right:
        count_chart(
            rank("submission_channel", "channels"),
            "category",
            "Submission channels",
            "#147d83",
            400,
        )
    with st.expander("All recorded locations"):
        display_table(states, ["complaints"])
        st.download_button(
            "Download location counts",
            states[["category", "complaints"]].to_csv(index=False),
            "location_counts.csv",
            "text/csv",
        )

st.caption(
    "K = thousand · M = million · B = billion. Display counts are rounded; CSV downloads retain exact values. Filters apply across all tabs; local issue drilldown is explicitly scoped."
)
with st.expander("Metric definitions"):
    st.markdown(
        "**Timely response rate:** timely responses ÷ records with known timeliness. **Narrative coverage:** published narratives ÷ complaints. **Complaint share:** category volume ÷ selected complaint total. Zero denominators yield N/A. These summaries do not contain narrative text or resolution duration; the AI agent is a later project stage."
    )
st.markdown(
    '<div class="footer">Financial Complaint Intelligence · Source: CFPB public complaint snapshot. Raw volumes do not establish company-wide incident rates or internal root causes.</div>',
    unsafe_allow_html=True,
)
