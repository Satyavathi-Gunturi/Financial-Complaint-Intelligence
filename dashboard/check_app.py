"""Verify refreshed snapshot totals and interactive dashboard filters."""

from pathlib import Path

import duckdb
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def compact(value):
    """Expected count presentation contract."""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"
    if value >= 1_000_000 or round(value / 1000) >= 1000:
        return f"{value / 1_000_000:.2f} M"
    return f"{value / 1000:.0f}K" if value >= 1000 else f"{value:.0f}"


with duckdb.connect() as con:
    con.read_parquet(str(ROOT / "dashboard_daily_company_product.parquet")).create_view(
        "source"
    )
    total, narratives, timely, known = con.execute(
        "SELECT SUM(complaint_count), SUM(narrative_count), SUM(timely_response_count), SUM(known_timeliness_count) FROM source"
    ).fetchone()
    mortgage = con.execute(
        "SELECT SUM(complaint_count) FROM source WHERE product='Mortgage'"
    ).fetchone()[0]
app = AppTest.from_file(
    str(Path(__file__).with_name("app.py")), default_timeout=60
).run()
assert not app.exception, app.exception
assert len(app.tabs) == 8
assert app.metric[0].value == compact(total)
assert app.metric[3].value == compact(narratives)
assert app.metric[1].value == (f"{100 * timely / known:.2f}%" if known else "N/A")
assert app.metric[2].value == f"{100 * narratives / total:.2f}%"
if mortgage:
    app.sidebar.multiselect[1].set_value(["Mortgage"]).run()
    assert not app.exception, app.exception
    assert app.metric[0].value == compact(mortgage)
app.sidebar.selectbox[0].set_value("Week").run()
assert not app.exception, app.exception
print("Snapshot totals, eight tabs, product filters and weekly trends passed.")
