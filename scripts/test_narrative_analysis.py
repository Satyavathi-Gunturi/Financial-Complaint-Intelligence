"""Check evidence integrity, topic accounting and filtered dashboard behavior."""

import sys
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
sys.path.insert(0, str(ROOT / "scripts"))
from executive_briefing import issue_summary, representative_quote  # noqa: E402
from export_narrative_sample import export_sample, file_hash  # noqa: E402
from narrative_analysis import discover, redact, theme_summary  # noqa: E402


def test_model():
    texts = [
        "Unauthorized credit card charge purchase merchant fraud transaction dispute",
        "Mortgage escrow payment property servicing interest loan foreclosure",
        "Debt collector collection harassment phone calls repeated debt collection",
    ]
    frame = pd.DataFrame(
        [
            dict(
                complaint_id=str(i),
                excerpt=texts[i % 3],
                period="Selected" if i < 150 else "Previous",
            )
            for i in range(300)
        ]
    )
    assigned, labels = discover(frame, topics=3)
    summary = theme_summary(assigned, labels)
    assert len(labels) == 3
    assert summary.narratives.sum() == 150
    assert abs(summary.share_pct.sum() - 100) < 1e-8
    assert (summary.change_pp.abs() < 1e-8).all()
    # Distinct financial subjects should not collapse to the same dominant topic.
    assert len(set(assigned.iloc[:3].topic)) == 3
    again, again_labels = discover(frame, topics=3)
    assert assigned.topic.tolist() == again.topic.tolist() and labels == again_labels
    empty, labels = discover(
        pd.DataFrame({"excerpt": ["xxxx"] * 20, "period": ["Selected"] * 20})
    )
    assert (empty.topic == -1).all() and not labels
    assert "person@example.com" not in redact(
        "Email person@example.com or call 123-456-7890"
    )
    sparse = assigned.iloc[:15].copy()
    assert theme_summary(sparse, again_labels).change_pp.isna().all()


def test_briefing():
    frame = pd.DataFrame(
        [
            {"issue": "Incorrect information", "period": "Selected", "topic": 0},
            {"issue": "Incorrect information", "period": "Selected", "topic": 1},
            {"issue": None, "period": "Selected", "topic": -1},
            {"issue": "Incorrect information", "period": "Previous", "topic": 0},
        ]
    )
    _, summary = issue_summary(frame)
    assert summary.narratives.sum() == 3
    assert abs(summary.share_pct.sum() - 100) < 1e-8
    assert summary.iloc[0].narratives == 2
    assert "Issue not recorded" in summary.concern.tolist()
    assert summary.change_pp.isna().all()
    text = "I found incorrect details on my credit report and disputed them. Section 999 describes legal provisions for this complaint."
    quote = representative_quote(text, "Incorrect information on your report")
    assert quote in text and "disputed" in quote


def test_export():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        database, overview = root / "test.duckdb", root / "overview.parquet"
        with duckdb.connect(str(database)) as con:
            con.execute("CREATE SCHEMA main_gold; CREATE SCHEMA main_silver")
            con.execute("""CREATE TABLE main_gold.complaint_metrics AS SELECT cast(range as varchar) complaint_id,
                DATE '2024-01-01' date_received, 'Example' company_name, 'Card' product,
                NULL::VARCHAR sub_product, 'Dispute' issue, 'TX' state,
                'Closed' company_response, 1 complaint_count, 1 narrative_count FROM range(40)""")
            con.execute("""CREATE TABLE main_silver.complaint_narratives AS SELECT complaint_id,
                'I dispute a card charge. Contact person@example.com.' narrative
                FROM main_gold.complaint_metrics""")
            con.execute(
                f"COPY (SELECT date_received,SUM(complaint_count)::BIGINT complaint_count, SUM(narrative_count)::BIGINT narrative_count FROM main_gold.complaint_metrics GROUP BY ALL) TO '{overview}' (FORMAT PARQUET)",
            )
        output = export_sample(database, overview, root / "evidence.parquet", limit=20)
        with duckdb.connect() as con:
            rows, ids, corpus, sha = con.execute(
                "SELECT COUNT(*),COUNT(DISTINCT complaint_id),MAX(corpus_narratives),MAX(overview_sha256) FROM read_parquet(?)",
                [str(output)],
            ).fetchone()
        assert rows == ids == 20 and corpus == 40 and sha == file_hash(overview)
        with duckdb.connect(str(database)) as con:
            con.execute(
                "INSERT INTO main_gold.complaint_metrics SELECT 'other',date_received,company_name,product,sub_product,issue,state,company_response,complaint_count,narrative_count FROM main_gold.complaint_metrics LIMIT 1"
            )
        try:
            export_sample(database, overview, root / "bad.parquet")
        except ValueError:
            pass
        else:
            raise AssertionError("Mismatched releases must not export")


def test_app():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=120).run()
    assert not app.exception, app.exception
    assert len(app.tabs) == 8
    app.toggle(key="run_narrative_analysis").set_value(True).run()
    assert not app.exception, app.exception
    assert app.selectbox(key="evidence_concern").options
    assert any("Executive briefing" in item.value for item in app.markdown)
    assert len(app.expander) >= 5
    app.text_input(key="evidence_phrase").set_value("unlikely-phrase-zzz").run()
    assert not app.exception, app.exception
    # Exercise a full prior window within source coverage, preserving product filters.
    app.sidebar.date_input[0].set_value(
        (pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-12-31").date())
    )
    app.sidebar.multiselect[1].set_value(["Mortgage"]).run()
    assert not app.exception, app.exception
    assert app.selectbox(key="evidence_concern").options
    assert app.dataframe


if __name__ == "__main__":
    test_model()
    test_export()
    test_briefing()
    if "--app" in sys.argv:
        test_app()
    print(
        "Narrative model, accounting, reproducibility, sparse evidence and export snapshot tests passed."
    )
