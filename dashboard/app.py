"""Explore the validated CFPB daily company/product complaint snapshot."""

import html
import json
import textwrap
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ai_workspace import render as render_ai
from complaint_insights import render as render_insights

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dashboard_daily_company_product.parquet"
DATASETS = {
    "overview": DATA,
    "issues": ROOT / "dashboard_issues.parquet",
    "geography": ROOT / "dashboard_geography.parquet",
    "channels": ROOT / "dashboard_channels.parquet",
    "narratives": ROOT / "dashboard_narratives.parquet",
}
st.set_page_config(
    page_title="Financial Complaint Intelligence", page_icon="◈", layout="wide"
)


@st.cache_data(show_spinner=False, max_entries=128)
def cached_query(sql, params, dataset, version):
    """Run parameterized analytics on the packaged Parquet snapshot."""
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.read_parquet(str(DATASETS[dataset])).create_view("metrics")
        return con.execute(sql, list(params)).fetchdf()


def query(sql, params=(), dataset="overview"):
    """Cache by file identity so published dataset replacements invalidate results."""
    path = DATASETS[dataset]
    info = path.stat()
    return cached_query(sql, params, dataset, (info.st_mtime_ns, info.st_size))


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
    "<style>" + Path(__file__).with_name("styles.css").read_text() + "</style>"
    '<div class="topbar"><span class="brand-mark" aria-hidden="true">◈</span>'
    '<span class="brand-title">Financial Complaint Intelligence</span>'
    '<span class="brand-subtitle">Executive dashboard</span>'
    '<span class="snapshot-badge">Validated snapshot</span></div>',
    unsafe_allow_html=True,
)


def style_chart(fig, height=340):
    """Apply a consistent, readable executive chart theme."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", color="#526773", size=12),
        margin=dict(l=20, r=24, t=30, b=35),
        colorway=["#087f8c", "#142b3b", "#63ada7", "#c5a46d", "#95a6b8"],
        hoverlabel=dict(bgcolor="#142b3b", font_color="white"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#eeece5", zeroline=False)
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
    st.markdown("### Refine your view")
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

with st.sidebar:
    manifest_path = ROOT / "reports/refresh_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        st.caption(
            f"Rolling {manifest['retention_months']}-month publication · "
            f"Coverage through {manifest['observed_last_date']} · "
            f"Last validated refresh: {manifest['validated_at'][:16].replace('T', ' ')} UTC"
        )
    else:
        st.caption(
            "Historical snapshot · Scheduled rolling refresh awaiting its first validated publication."
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


def headline_metrics():
    """Repeat the shared selection summary within each analytical tab."""
    st.markdown(
        f'<div class="scope">SELECTED VIEW · {dates[0]:%d %b %Y} — {dates[1]:%d %b %Y} · {len(companies) if companies else "All"} companies · {len(products) if products else "All"} products</div>',
        unsafe_allow_html=True,
    )
    cards = st.columns(4)
    cards[0].metric("Complaints", compact(totals["complaints"]))
    cards[1].metric("Timely response rate", rate(totals["timely"], totals["known"]))
    cards[2].metric(
        "Narrative coverage", rate(totals["narratives"], totals["complaints"])
    )
    cards[3].metric("Published narratives", compact(totals["narratives"]))
    st.caption(
        f"Timeliness denominator: {compact(totals['known'])} known records · Unknown timeliness: {compact(totals['unknown'])}. Rates are calculated after aggregation."
    )


def count_chart(frame, category, title, color="#142b3b", height=400):
    """Render ranked values with compact labels and full category tooltips."""
    frame = frame.copy().sort_values("complaints")
    frame["label"] = frame[category].fillna("Missing label").map(str)

    def wrap_label(value):
        lines = textwrap.wrap(value, width=24)
        if len(lines) > 2:
            lines = [lines[0], lines[1][:21] + "…"]
        return "<br>".join(html.escape(line) for line in lines)

    frame["short"] = frame["label"].map(wrap_label)
    frame["count_label"] = frame["complaints"].map(compact)
    stem_x, stem_y = [], []
    for value, label in zip(frame["complaints"], frame["short"]):
        stem_x.extend([0, value, None])
        stem_y.extend([label, label, None])
    fig = style_chart(go.Figure(), height)
    fig.add_trace(
        go.Scatter(
            x=stem_x,
            y=stem_y,
            mode="lines",
            line=dict(color=color, width=3),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frame["complaints"],
            y=frame["short"],
            mode="markers+text",
            marker=dict(color=color, size=11),
            text=frame["count_label"],
            textposition="middle right",
            customdata=frame[["label", "count_label"]],
            cliponaxis=False,
            showlegend=False,
            hovertemplate="<b>%{customdata[0]}</b><br>Complaints: %{customdata[1]}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Complaints", tickangle=0, nticks=3)
    fig.update_yaxes(tickfont=dict(size=11), automargin=True)
    maximum = frame["complaints"].max()
    ticks = [maximum * i / 2 for i in range(3)]
    fig.update_xaxes(
        tickvals=ticks, ticktext=[compact(v) for v in ticks], range=[0, maximum * 1.25]
    )
    fig.update_layout(margin=dict(l=150, r=35, t=25, b=45))
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
            color_discrete_sequence=["#087f8c"],
            labels={"period": "Received period", "complaints": "Complaints"},
        )
    )
    fig.update_traces(
        line_width=2.5,
        marker_size=5,
        fillcolor="rgba(8,127,140,.12)",
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

(
    overview,
    trends,
    company_tab,
    issues_tab,
    response_tab,
    geo_tab,
    insights_tab,
) = st.tabs(
    [
        ":material/home: Overview",
        ":material/bar_chart: Trends",
        ":material/apartment: Companies",
        ":material/inventory_2: Products & Issues",
        ":material/chat_bubble: Responses",
        ":material/location_on: Geography & Channels",
        ":material/description: Narratives",
    ]
)

with overview:
    headline_metrics()
    st.subheader("Complaint demand at a glance")
    demand, concentration = st.columns([1.5, 1], gap="medium")
    with demand:
        st.markdown("**Complaint demand over time**")
        trend_chart(trend, "overview_trend")
    with concentration:
        count_chart(
            rank("product", limit=5),
            "category",
            "Product concentration",
            "#087f8c",
            340,
        )
    st.caption(
        "Received-date counts. First and last buckets may be partial. Public complaint volume is not normalized by company size or customer count."
    )
    with st.expander("Leading companies by volume"):
        count_chart(
            rank("company_name", limit=5),
            "category",
            "Company concentration",
            height=290,
        )
    top5 = rank("company_name", limit=5)["complaints"].sum()
    st.caption(
        f"Top five companies account for {100 * top5 / totals['complaints']:.2f}% of complaints in the selected view. Concentration is a volume measure, not a company performance rating."
    )

with trends:
    headline_metrics()
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
            color_discrete_sequence=["#c5a46d"],
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
    headline_metrics()
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
    headline_metrics()
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
        color_discrete_sequence=["#142b3b", "#087f8c", "#63ada7", "#c5a46d"],
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
            "#087f8c",
            430,
        )
    st.caption(
        "The issue selection applies to these two drilldown charts. Product treemap and headline KPIs retain the global filters. Missing labels are retained; source product labels are not merged."
    )

with response_tab:
    headline_metrics()
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
                "#142b3b",
                "#c5a46d",
                "#087f8c",
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
    headline_metrics()
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
        color_continuous_scale=["#e3efef", "#087f8c", "#142b3b"],
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
            "#087f8c",
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

with insights_tab:
    headline_metrics()
    render_insights(ROOT, query, where, params, dates, totals, compact, rate)

with st.container(key="ai_launcher"):
    chat = st.popover(
        "Ask AI Analyst",
        icon=":material/auto_awesome:",
        type="primary",
        key="ai_chat_open",
        on_change="rerun",
    )
    if chat.open:
        with chat:
            render_ai(
                ROOT,
                {
                    "start_date": dates[0].isoformat(),
                    "end_date": dates[1].isoformat(),
                    "company_name": companies,
                    "product": products,
                    "sub_product": subs,
                },
            )

st.caption(
    "K = thousand · M = million · B = billion. Display counts are rounded; CSV downloads retain exact values. Filters apply across all tabs; local issue drilldown is explicitly scoped."
)
with st.expander("Metric definitions"):
    st.markdown(
        "**Timely response rate:** timely responses ÷ records with known timeliness. **Narrative coverage:** published narratives ÷ complaints. **Complaint share:** category volume ÷ selected complaint total. Zero denominators yield N/A. Aggregate tabs do not contain narrative text or resolution duration. Complaint Insights analyzes sampled narrative excerpts. AI Analyst combines business context, constrained aggregate SQL and sampled evidence when configured."
    )
st.markdown(
    '<div class="footer">Financial Complaint Intelligence · Source: CFPB public complaint snapshot. Raw volumes do not establish company-wide incident rates or internal root causes.</div>',
    unsafe_allow_html=True,
)
