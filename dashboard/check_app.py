"""Validate real snapshot totals and interactive dashboard filter execution."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

app = AppTest.from_file(
    str(Path(__file__).with_name("app.py")), default_timeout=60
).run()
assert not app.exception, app.exception
assert app.metric[0].value == "14.48 M"
assert app.metric[3].value == "2.71 M"
assert app.metric[1].value == "99.59%"
assert app.metric[2].value == "18.72%"
app.sidebar.multiselect[1].set_value(["Mortgage"]).run()
assert not app.exception, app.exception
assert app.metric[0].value == "95K"
app.sidebar.selectbox[0].set_value("Week").run()
assert not app.exception, app.exception
app.sidebar.date_input[0].set_value(("2026-08-01", "2026-08-31")).run()
assert not app.exception, app.exception
print("Snapshot totals, product filters, weekly trends and date filters passed.")
