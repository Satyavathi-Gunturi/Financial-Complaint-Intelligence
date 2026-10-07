"""Filtered, evidence-backed narrative exploration for the executive dashboard."""

import hashlib
from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from narrative_analysis import discover, theme_summary


@st.cache_data(show_spinner=False, max_entries=8)
def analyze(frame):
    return discover(frame)


@st.cache_data(show_spinner=False, max_entries=8)
def snapshot_hash(path, version):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def render(root, query, where, params, dates, totals, compact, rate):
    st.subheader("The experiences behind the numbers")
    st.caption(
        "Local NLP theme discovery · Customer-reported experiences · Supporting excerpts"
    )
    path = root / "dashboard_narratives.parquet"
    if not path.exists():
        st.info(
            "Narrative analysis is awaiting its first evidence export. The existing dashboard remains available."
        )
        st.markdown(
            "Export the saved narrative checkpoint using the [Colab instructions](https://github.com/Satyavathi-Gunturi/Financial-Complaint-Intelligence/blob/main/docs/complaint-insights.md)."
        )
        return
    meta = query(
        "SELECT overview_sha256, corpus_narratives FROM metrics LIMIT 1",
        dataset="narratives",
    )
    if meta.empty:
        st.info("This release contains no published narrative excerpts.")
        return
    overview = root / "dashboard_daily_company_product.parquet"
    version = (overview.stat().st_mtime_ns, overview.stat().st_size)
    if meta.iloc[0]["overview_sha256"] != snapshot_hash(str(overview), version):
        st.warning(
            "Narrative evidence belongs to a different dashboard release. Analysis is unavailable until a matching export is published."
        )
        return
    matched = int(
        query("SELECT COUNT(*) AS n FROM metrics" + where, params, "narratives").iloc[
            0
        ]["n"]
    )
    a, b, c = st.columns(3)
    a.metric("Filtered published narratives", compact(totals["narratives"]))
    b.metric("Narrative coverage", rate(totals["narratives"], totals["complaints"]))
    c.metric("Matching exported excerpts", compact(matched))
    st.caption(
        "The export is a global, deterministic sample of up to 60K narrative-bearing complaints. "
        "It is not balanced by company or product. Narrow filters may have few or no examples. "
        "Theme counts describe sampled excerpts, never all complaints."
    )
    if matched < 20:
        st.info(
            "At least 20 matching excerpts are needed for theme discovery. Broaden the filters."
        )
        return
    if not st.toggle("Analyze selected narratives", key="run_narrative_analysis"):
        st.caption(
            "Enable analysis to discover themes within the current date, company, product and sub-product filters."
        )
        return
    start, end = dates
    prior_end = start - timedelta(days=1)
    prior_start = prior_end - (end - start)
    sql = "SELECT complaint_id, date_received, company_name, product, sub_product, issue, state, excerpt, excerpt_truncated FROM metrics"
    sql += where + " ORDER BY md5(complaint_id), complaint_id LIMIT 3000"
    current = query(sql, params, "narratives").assign(period="Selected")
    first_date = (
        query("SELECT MIN(date_received) AS first FROM metrics").iloc[0]["first"].date()
    )
    if prior_start < first_date:
        previous = current.iloc[:0].copy().assign(period="Previous")
        st.caption(
            "Prior-period comparison is unavailable because its full date window precedes the snapshot coverage."
        )
    else:
        previous = query(
            sql, (prior_start, prior_end) + params[2:], "narratives"
        ).assign(period="Previous")
    with st.spinner("Finding recurring language and supporting evidence…"):
        assigned, labels = analyze(pd.concat([current, previous], ignore_index=True))
    summary = theme_summary(assigned, labels)
    analyzed = len(current)
    st.caption(
        f"Analyzed {compact(analyzed)} selected excerpts and {compact(len(previous))} prior-period excerpts "
        f"({prior_start:%d %b %Y}–{prior_end:%d %b %Y}). Up to 3K per period; "
        "the same model discovers themes across both periods. Excerpts use the first 2K characters; "
        "additional email/link/number masking is applied. Names and other personal details may remain."
    )
    unassigned = int(
        ((assigned["period"] == "Selected") & (assigned["topic"] == -1)).sum()
    )
    if summary.empty:
        st.info(
            "The excerpts do not contain enough recurring terms to discover useful themes."
        )
        return
    first = summary.iloc[0]
    st.markdown(f"**Leading language theme:** {first['theme']}")
    st.write(
        f"{compact(first['narratives'])} excerpts ({first['share_pct']:.1f}% of the analyzed selection) "
        "have this as their strongest learned theme. Inspect the examples before interpreting the label."
    )
    summary["count_label"] = summary["narratives"].map(compact)
    chart = px.treemap(
        summary,
        path=["theme"],
        values="narratives",
        color="share_pct",
        color_continuous_scale="Teal",
        custom_data=["count_label", "share_pct"],
    )
    chart.update_traces(
        texttemplate="%{label}<br>%{customdata[0]}",
        hovertemplate="%{label}<br>Sampled excerpts: %{customdata[0]}<br>Share of analyzed selection: %{customdata[1]:.1f}%<extra></extra>",
    )
    chart.update_layout(
        margin=dict(t=10, l=0, r=0, b=0), height=340, coloraxis_showscale=False
    )
    st.plotly_chart(chart, width="stretch", key="narrative_themes")
    st.caption(
        f"{compact(unassigned)} selected excerpts had no usable model vocabulary and remain unassigned. "
        "Each other excerpt contributes once, to its strongest theme. Labels are learned terms, not verified causes."
    )
    changes = summary.dropna(subset=["change_pp"]).sort_values(
        "change_pp", ascending=False
    )
    st.markdown("**Changes in sampled theme share**")
    if changes.empty:
        st.caption(
            "Comparison is unavailable: require at least 50 analyzed excerpts in each period and 10 supporting excerpts per theme in each period."
        )
    else:
        display = changes[["theme", "count_label", "share_pct", "change_pp"]].copy()
        display["share_pct"] = display["share_pct"].map(lambda x: f"{x:.1f}%")
        display["change_pp"] = display["change_pp"].map(lambda x: f"{x:+.1f} pp")
        st.dataframe(
            display.rename(
                columns={
                    "theme": "Learned theme",
                    "count_label": "Sampled excerpts",
                    "share_pct": "Selected share",
                    "change_pp": "Share change",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Percentage-point changes describe this sample; they are not significance tests or population trend estimates."
        )
    st.download_button(
        "Download theme counts (exact values)",
        summary.drop(columns=["count_label"]).to_csv(index=False),
        "complaint_theme_counts.csv",
        "text/csv",
        key="download_narrative_themes",
    )
    st.markdown("**Explore the supporting evidence**")
    selected = st.selectbox(
        "Learned theme",
        summary["topic"].tolist(),
        format_func=lambda value: labels[value],
        key="evidence_theme",
    )
    search = st.text_input(
        "Find a phrase in the analyzed excerpts", key="evidence_phrase", max_chars=100
    )
    evidence = assigned[
        (assigned["period"] == "Selected") & (assigned["topic"] == selected)
    ]
    if search.strip():
        evidence = evidence[
            evidence["excerpt"].str.contains(search.strip(), case=False, regex=False)
        ]
    st.caption(
        f"{compact(len(evidence))} matching analyzed excerpts · Showing up to five with the strongest theme weight."
    )
    for _, row in (
        evidence.sort_values(["weight", "complaint_id"], ascending=[False, True])
        .head(5)
        .iterrows()
    ):
        with st.expander(
            f"Complaint {row['complaint_id']} · {pd.Timestamp(row['date_received']):%d %b %Y}"
        ):
            st.write(
                f"Company: {row['company_name']} · Product: {row['product']} · Issue: {row['issue']}"
            )
            st.text(row["excerpt"])
            if row["excerpt_truncated"]:
                st.caption(
                    "Excerpt truncated at 2K characters; analysis uses the excerpt."
                )
    with st.expander("How to interpret these insights"):
        st.write(
            "TF–IDF and non-negative matrix factorization discover recurring language without labeled training data. "
            "This is an unsupervised machine-learning component, not an LLM agent. It does not infer sentiment, "
            "prove misconduct, measure financial loss or diagnose root causes. Theme weights are not confidence probabilities. "
            "Model labels may overlap or reflect boilerplate; human review of cited IDs and excerpts is required. "
            "Themes are fitted to each filtered selection and its prior period, so labels can change when filters change."
        )
