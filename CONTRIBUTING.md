# Coding and documentation conventions

Use Python 3.12, matching CI and the Streamlit deployment. Python follows PEP 8 with Ruff formatting, sorted imports, 88-character target lines and descriptive module/function docstrings. SQL/Jinja follows sqlfmt's consistent layout and lowercase keywords. Long literals may exceed the target line length. YAML uses two-space indentation.

## Comments and model documentation
Every model begins with its grain and purpose. Explain non-obvious decisions: preserving NULLs, stable JSON keys, date roles, missing-value denominators and tag multiplicity. Avoid comments that merely repeat SQL syntax. Schema YAML documents models and tested columns; metric meanings are in docs/metric-definitions.md.

Keep metric inputs additive. Calculate rates after aggregation. Do not introduce row filters, corporate-name merging or inferred root causes without documenting and testing the change. Date-received is the default analytics time field; ISO week requires ISO year.

## Checks before committing
```bash
pip install -r requirements-dev.txt
ruff check scripts dashboard
ruff format --check scripts dashboard
sqlfmt --check dbt/models dbt/tests
python scripts/smoke_test.py
python dashboard/check_app.py
python scripts/test_narrative_analysis.py --app
python scripts/test_ai_agent.py --app
```

The notebook is a documented historical Colab workflow. The extracted dbt files are the maintained SQL implementation; notebook generators can regenerate the original, less-formatted SQL. Keep outputs and widget metadata cleared before publishing. Never publish private runtime profiles, credentials or large data.

Use small commits explaining the problem and behavior. Update design/metric documentation when behavior changes. Preserve both wide gold and star structures until comparative agent evaluation is complete. Describe full-data Colab results separately from synthetic smoke tests.

## Branch and pull request workflow

Create a descriptive feature or fix branch from current main. Commit changes to that branch, open a pull request with validation evidence, and merge using a merge commit after checks pass. Do not push implementation or dataset changes directly to main. Scheduled data releases follow the same branch → PR → merge flow. Preserve existing history; do not rewrite earlier direct commits to simulate PRs.
