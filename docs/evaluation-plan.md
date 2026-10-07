# Data-agent validation and planned evaluation

Offline aggregate-tool and Streamlit UI tests are implemented in `scripts/test_ai_agent.py --app`. The owner confirmed live Gemini access and supplied two example response screenshots on 2026-10-07; these do not establish systematic answer accuracy. No wide-versus-star agent benchmark has been executed yet. The goal is to compare wide gold and star queries using the same complaints, flags, definitions, model, prompt budget and tool limits.

## Question coverage
Daily/weekly/monthly counts; custom date windows; company/product/issue filters; timeliness rates; missing outcome handling; ISO week/year boundaries; tag filtering without double counting; partial periods; narrative coverage; evidence-backed narrative explanations; requests the dataset cannot answer.

## Method
Create a versioned question set with manually verified ground-truth SQL and expected results. Keep evaluation questions separate from prompt development examples. Execute each question against both structures using equivalent schema documentation, counterbalanced order and repeated runs. Compare result values and filters rather than literal generated SQL text. Record dataset revision, model version, prompt, tool calls, latency, errors and cost where applicable.

## Measures
Numerical accuracy, valid SQL execution rate, join/double-counting errors, correct date/denominator selection, end-to-end latency and SQL execution time separately. Narrative answers additionally require citation support, filter consistency, appropriate uncertainty and abstention for unavailable facts. Account for warm/cold caches and query plans before attributing latency differences to table layout.

Star flags currently derive from wide gold, so this evaluates query representation, not independent metric-pipeline implementations. Root cause, customer satisfaction and financial-loss questions require abstention or an explicit statement of unavailable evidence.
