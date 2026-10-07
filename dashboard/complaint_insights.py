"""Filtered, evidence-backed narrative exploration for the executive dashboard."""

import hashlib
import html
import re
from datetime import timedelta

import pandas as pd
import streamlit as st
from executive_briefing import (
    investigation_question,
    issue_summary,
    representative_quote,
)
from narrative_analysis import discover


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
    st.subheader("Customer complaint briefing")
    st.caption("What customers report, what is changing, and where to investigate.")
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
    st.caption(
        f"{compact(totals['narratives'])} published narratives · "
        f"{rate(totals['narratives'], totals['complaints'])} narrative coverage · "
        f"{compact(matched)} matching sample excerpts"
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
    assigned, summary = issue_summary(assigned)
    analyzed = len(current)
    if summary.empty:
        st.info("No evidence is available for this selection.")
        return
    summary["count_label"] = summary["narratives"].map(compact)
    changes = summary.dropna(subset=["change_pp"]).sort_values(
        "change_pp", ascending=False
    )
    leading = summary.iloc[0]
    top_three = summary.head(3)
    st.markdown("### Executive briefing")
    st.caption(
        f"Based on {compact(analyzed)} analyzed sample excerpts. Findings describe customer reports, not verified company-wide incidents."
    )
    with st.container(border=True):
        st.markdown(
            f"**The largest recorded concern is {leading['concern'].lower()}.**"
        )
        st.write(
            f"It accounts for {leading['share_pct']:.1f}% of the analyzed sample "
            f"({compact(leading['narratives'])} excerpts)."
        )
        st.write(
            f"The three largest recorded issues account for {top_three['share_pct'].sum():.1f}% "
            "of this sample. These categories provide the first areas for evidence review."
        )
        if not changes.empty:
            change = changes.iloc[0]
            if change["change_pp"] > 0:
                st.write(
                    f"The largest supported increase in sample share is {change['concern'].lower()}: "
                    f"+{change['change_pp']:.1f} percentage points versus the previous period."
                )
            else:
                st.write(
                    "No issue with sufficient support gained share versus the previous period."
                )
        else:
            st.write(
                "A supported period-over-period comparison is unavailable for this selection."
            )
    st.markdown("### Main customer concerns")
    st.caption(
        "Ranked by recorded issue in the analyzed sample. Each excerpt contributes once; select a concern below to inspect more evidence."
    )
    for index, (_, row) in enumerate(summary.head(6).iterrows()):
        if index % 2 == 0:
            columns = st.columns(2)
        with columns[index % 2], st.container(border=True):
            st.markdown(f"**{row['concern']}**")
            st.metric(
                "Sampled excerpts",
                compact(row["narratives"]),
                delta=f"{row['change_pp']:+.1f} pp"
                if pd.notna(row["change_pp"])
                else None,
                delta_color="off",
                help="Count in the analyzed sample. Change is in sample share, not full complaint volume.",
            )
            st.caption(f"{row['share_pct']:.1f}% of analyzed excerpts")
            group = assigned[
                (assigned.period == "Selected") & (assigned.concern == row["concern"])
            ]
            evidence_row = group.sort_values(
                ["weight", "complaint_id"], ascending=[False, True]
            ).iloc[0]
            quote = representative_quote(evidence_row["excerpt"], row["concern"])
            st.markdown(
                '<blockquote style="margin:10px 0;padding:8px 12px;border-left:3px solid #168b88;font-size:14px;color:#334155">'
                + html.escape(quote)
                + "</blockquote>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"Complaint {evidence_row['complaint_id']} · {pd.Timestamp(evidence_row['date_received']):%d %b %Y}"
            )
    st.markdown("### What changed")
    if changes.empty:
        st.caption(
            "Choose a shorter date range within the snapshot to enable a prior-period comparison. Some concerns may still have too few examples to compare."
        )
    else:
        for _, row in (
            changes.reindex(changes.change_pp.abs().sort_values(ascending=False).index)
            .head(3)
            .iterrows()
        ):
            direction = (
                "Gained"
                if row.change_pp > 0
                else "Lost"
                if row.change_pp < 0
                else "Unchanged by"
            )
            st.write(
                f"**{row.concern}** — {direction.lower()} {abs(row.change_pp):.1f} pp of sample share "
                f"({compact(row.prior_narratives)} prior → {compact(row.narratives)} selected excerpts)."
            )
        st.caption(
            "Changes describe sample composition, not statistical significance or full-population trends."
        )
    st.markdown("### Areas to investigate")
    st.caption(
        "Questions for evidence review; these are not established root causes or recommendations to act against a company."
    )
    for _, row in top_three.iterrows():
        st.write(f"**{row.concern}:** {investigation_question(row.concern)}")
    st.markdown("### Language behind the concerns")
    st.caption(
        "Discovered word clusters · Larger phrases appear in more excerpts within their cluster. Counts overlap when an excerpt mentions several phrases."
    )
    palettes = [("#edf9f8", "#087f8c"), ("#f2efff", "#6854b8"), ("#fff5e5", "#926022")]
    for index, (topic, label) in enumerate(labels.items()):
        group = assigned[(assigned.period == "Selected") & (assigned.topic == topic)]
        if group.empty:
            continue
        if index % 3 == 0:
            cluster_columns = st.columns(3)
        terms = label.split(" · ")
        counts = [
            (
                term,
                int(
                    group.excerpt.str.contains(
                        r"\b" + re.escape(term) + r"\b", case=False, regex=True
                    ).sum()
                ),
            )
            for term in terms
        ]
        largest = max((count for _, count in counts), default=1) or 1
        background, color = palettes[index % 3]
        chips = "".join(
            f'<span title="{html.escape(term)}: {compact(count)} excerpts mentioning this phrase" '
            f'style="display:inline-block;padding:8px 10px;margin:4px;border-radius:14px;background:white;'
            f'color:{color};font-size:{15 + 13 * count / largest:.0f}px;font-weight:650;line-height:1.25">'
            f'{html.escape(term)} <small style="font-size:11px;font-weight:500">{compact(count)}</small></span>'
            for term, count in counts
            if count
        )
        with cluster_columns[index % 3]:
            st.markdown(
                f'<div style="background:{background};border:1px solid {color}25;border-radius:18px;padding:18px;min-height:210px;margin-bottom:14px">'
                f'<div style="color:{color};font-size:12px;font-weight:700;letter-spacing:1px">WORD CLUSTER {topic + 1}</div>'
                f'<div style="margin:7px 0 10px;color:#334155;font-size:13px">{compact(len(group))} sampled excerpts</div>'
                f"<div>{chips}</div></div>",
                unsafe_allow_html=True,
            )
    cluster_options = [-1] + list(labels)
    cluster_choice = st.selectbox(
        "Word cluster for evidence review",
        cluster_options,
        format_func=lambda topic: "All word clusters"
        if topic == -1
        else f"Cluster {topic + 1} · {labels[topic]}",
        key="evidence_cluster",
    )
    st.markdown("### Explore customer evidence")
    selected = st.selectbox(
        "Customer concern", summary.concern.tolist(), key="evidence_concern"
    )
    search = st.text_input(
        "Find a phrase in the analyzed excerpts", key="evidence_phrase", max_chars=100
    )
    evidence = assigned[
        (assigned.period == "Selected") & (assigned.concern == selected)
    ]
    if cluster_choice != -1:
        evidence = evidence[evidence.topic == cluster_choice]
    if search.strip():
        evidence = evidence[
            evidence.excerpt.str.contains(search.strip(), case=False, regex=False)
        ]
    st.caption(
        f"{compact(len(evidence))} matching analyzed excerpts · Showing up to five."
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
    st.download_button(
        "Download concern counts (exact values)",
        summary.drop(columns=["count_label"]).to_csv(index=False),
        "complaint_concern_counts.csv",
        "text/csv",
        key="download_narrative_themes",
    )
    with st.expander("Analysis coverage and recurring language"):
        st.write(
            f"Analyzed {compact(analyzed)} selected and {compact(len(previous))} prior-period excerpts "
            f"({prior_start:%d %b %Y}–{prior_end:%d %b %Y})."
        )
        st.write(
            "The export is a global deterministic sample of up to 60K public narratives, not balanced by company or product. "
            "Up to 3K matching excerpts are analyzed per period. Evidence uses the first 2K characters, with additional email/link/number masking; other personal details may remain."
        )
        st.write(
            "Executive concern counts and labels use the recorded source issue, including missing issues. "
            "NLP identifies recurring language and ranks supporting evidence; its clusters may overlap source issues or reflect boilerplate."
        )
        st.caption(
            "Comparison requires full prior-window coverage, 50 analyzed excerpts per period, and 10 examples of a concern in each period."
        )
        for topic, label in labels.items():
            count = int(
                ((assigned.period == "Selected") & (assigned.topic == topic)).sum()
            )
            if count:
                st.write(f"{label} · {compact(count)} sample excerpts")
    with st.expander("How to interpret these insights"):
        st.write(
            "TF–IDF and non-negative matrix factorization discover recurring language without labeled training data. "
            "This is an unsupervised machine-learning component, not an LLM agent. It does not infer sentiment, "
            "prove misconduct, measure financial loss or diagnose root causes. Theme weights are not confidence probabilities. "
            "Model labels may overlap or reflect boilerplate; human review of cited IDs and excerpts is required. "
            "Themes are fitted to each filtered selection and its prior period, so labels can change when filters change."
        )
