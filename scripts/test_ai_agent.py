"""Offline evaluations of SQL accounting, scope, tools and Gemini protocol."""

import asyncio
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import duckdb
import httpx
import pandas as pd
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
from agent_tools import DOCUMENTS, FILES, FLAGS, AgentTools  # noqa: E402
from ai_agent import DEFAULT_MODEL, run_agent  # noqa: E402


def metric_args(**changes):
    args = dict(
        dataset="overview",
        group_by=[],
        metrics=["complaint_count", "timely_response_rate"],
        interval="month",
        filters=[],
        start_date=None,
        end_date=None,
        order_by="complaint_count",
        descending=True,
        limit=10,
    )
    args.update(changes)
    return args


def fixture(root):
    records = []
    for received, company, product, count, timely, known in [
        ("2024-01-01", "A", "Card", 10, 8, 8),
        ("2024-01-02", "A", "Card", 20, 10, 20),
        ("2024-01-02", "B", "Mortgage", 100, 90, 100),
    ]:
        row = {flag: 0 for flag in FLAGS}
        row.update(
            date_received=pd.Timestamp(received),
            company_name=company,
            product=product,
            sub_product=None,
            complaint_count=count,
            timely_response_count=timely,
            known_timeliness_count=known,
            narrative_count=1,
        )
        records.append(row)
    overview = pd.DataFrame(records)
    for dataset, filename in FILES.items():
        if dataset == "narratives":
            continue
        frame = overview.copy()
        extras = {
            "issues": {"issue": "Dispute", "sub_issue": None},
            "geography": {"state": "TX"},
            "channels": {"submission_channel": "Web"},
        }
        for column, value in extras.get(dataset, {}).items():
            frame[column] = value
        frame.to_parquet(root / filename, index=False)
    sha = hashlib.sha256((root / FILES["overview"]).read_bytes()).hexdigest()
    pd.DataFrame(
        [
            dict(
                complaint_id="100",
                date_received=pd.Timestamp("2024-01-02"),
                company_name="A",
                product="Card",
                sub_product=None,
                issue="Dispute",
                excerpt="I disputed this credit card charge. Email person@example.com",
                excerpt_truncated=False,
                overview_sha256=sha,
                corpus_narratives=3,
            )
        ]
    ).to_parquet(root / FILES["narratives"], index=False)
    for filename in DOCUMENTS.values():
        path = root / filename
        path.parent.mkdir(exist_ok=True)
        path.write_text("CFPB source. Timely response rate uses known timeliness.")
    return AgentTools(
        root,
        dict(
            start_date="2024-01-01",
            end_date="2024-01-02",
            company_name=[],
            product=["Card"],
            sub_product=[],
        ),
    )


def rejects(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError("Invalid operation was not rejected")


def test_queries(tools):
    result = tools.query_metrics(**metric_args())
    assert result["rows"][0]["complaint_count"] == 30
    assert abs(result["rows"][0]["timely_response_rate"] - 100 * 18 / 28) < 1e-8
    assert "SUM(complaint_count)" in result["sql"]
    narrowed = tools.query_metrics(**metric_args(start_date="2024-01-02"))
    assert narrowed["rows"][0]["complaint_count"] == 20
    assert (
        tools.query_metrics(
            **metric_args(filters=[{"column": "sub_product", "values": [None]}])
        )["rows"][0]["complaint_count"]
        == 30
    )
    injected = tools.query_metrics(
        **metric_args(
            filters=[
                {"column": "company_name", "values": ["A'); DROP TABLE metrics; --"]}
            ]
        )
    )
    assert injected["rows"][0]["complaint_count"] is None
    assert "DROP" not in injected["sql"]
    assert tools.query_metrics(**metric_args())["rows"][0]["complaint_count"] == 30
    for changed in [
        dict(metrics=["read_csv('/etc/passwd')"]),
        dict(group_by=["state"]),
        dict(dataset="issues", group_by=["issue", "state"]),
        dict(start_date="2023-01-01"),
        dict(order_by="1;COPY"),
        dict(limit=51),
    ]:
        rejects(lambda changed=changed: tools.query_metrics(**metric_args(**changed)))
    rejects(lambda: tools.dispatch("execute_sql", {"sql": "DELETE FROM metrics"}))
    rejects(lambda: tools.read_business_document("../../.env"))
    groups = tools.query_metrics(
        **metric_args(group_by=["period"], interval="day", limit=1)
    )
    assert groups["truncated"] and len(groups["rows"]) == 1
    zero = tools.query_metrics(
        **metric_args(filters=[{"column": "company_name", "values": ["absent"]}])
    )
    assert zero["rows"][0]["timely_response_rate"] is None


def test_evidence(tools):
    result = tools.search_narratives("disputed", "Dispute", 5)
    assert result["matching_sample_excerpts"] == 1
    assert result["rows"][0]["complaint_id"] == "100"
    assert "person@example.com" not in result["rows"][0]["excerpt"]
    assert not tools.search_narratives("absent", None, 5)["rows"]
    path = tools.root / FILES["narratives"]
    frame = pd.read_parquet(path)
    frame["overview_sha256"] = "wrong"
    frame.to_parquet(path, index=False)
    rejects(lambda: tools.search_narratives("", None, 5))


def response(parts):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=parts),
                finish_reason=types.FinishReason.STOP,
            )
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=50, candidates_token_count=20
        ),
    )


class FakeGemini:
    """Use real SDK messages/schemas, execute real query tools, never network."""

    def __init__(self, bad_citation=False, expected=30):
        self.models = self
        self.calls = []
        self.bad_citation = bad_citation
        self.expected = expected

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            assert kwargs["config"].automatic_function_calling.disable
            assert kwargs["config"].tool_config.function_calling_config.mode == "ANY"
            return response(
                [
                    types.Part(
                        function_call=types.FunctionCall(
                            id="call-1", name="query_metrics", args=metric_args()
                        )
                    )
                ]
            )
        if len(self.calls) == 2:
            assert kwargs["contents"][-1].parts[0].function_response.id == "call-1"
            actual = kwargs["contents"][-1].parts[0].function_response.response
            assert actual["result"]["rows"][0]["complaint_count"] == self.expected
            return response([types.Part.from_text(text="Ready to answer.")])
        answer = {
            "sections": [
                {
                    "text": f"The selected data contains {self.expected} complaints.",
                    "source_ids": ["S999" if self.bad_citation else "S1"],
                }
            ],
            "limitations": "Selected snapshot only.",
            "next_question": "",
        }
        assert kwargs["config"].response_mime_type == "application/json"
        return response([types.Part.from_text(text=json.dumps(answer))])


def test_loop(tools):
    result = run_agent(
        FakeGemini(), DEFAULT_MODEL, "How many complaints?", [], tools, "CFPB glossary"
    )
    assert result["sources"][0]["result"]["rows"][0]["complaint_count"] == 30
    assert result["input_tokens"] == 150
    rejects(
        lambda: run_agent(
            FakeGemini(True), DEFAULT_MODEL, "How many?", [], tools, "CFPB"
        )
    )


def test_sdk_transport(tools):
    requests = []

    def handle(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert request.url.host == "generativelanguage.googleapis.com"
        if len(requests) == 1:
            declarations = payload["tools"][0]["functionDeclarations"]
            assert {item["name"] for item in declarations} == {
                "inspect_datasets",
                "read_business_document",
                "query_metrics",
                "search_narratives",
            }
            assert payload["toolConfig"]["functionCallingConfig"]["mode"] == "ANY"
            part = {
                "functionCall": {
                    "id": "transport-call",
                    "name": "query_metrics",
                    "args": metric_args(),
                }
            }
        elif len(requests) == 2:
            actual = payload["contents"][-1]["parts"][0]["functionResponse"]
            assert actual["response"]["result"]["rows"][0]["complaint_count"] == 30
            assert actual["id"] == "transport-call"
            part = {"text": "Ready to answer."}
        else:
            assert payload["generationConfig"]["responseMimeType"] == "application/json"
            assert payload["generationConfig"]["responseJsonSchema"]["properties"][
                "sections"
            ]
            part = {
                "text": json.dumps(
                    {
                        "sections": [{"text": "30 complaints.", "source_ids": ["S1"]}],
                        "limitations": "Selected filters.",
                        "next_question": "",
                    }
                )
            }
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"role": "model", "parts": [part]},
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    async_transport = httpx.AsyncClient(
        transport=httpx.MockTransport(handle), trust_env=False
    )
    with httpx.Client(
        transport=httpx.MockTransport(handle), trust_env=False
    ) as transport:
        with genai.Client(
            api_key="offline-test-key",
            vertexai=False,
            http_options=types.HttpOptions(
                httpx_client=transport,
                httpx_async_client=async_transport,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        ) as client:
            result = run_agent(
                client, DEFAULT_MODEL, "How many?", [], tools, "CFPB glossary"
            )
    asyncio.run(async_transport.aclose())
    assert len(requests) == 3 and result["sources"][0]["source_id"] == "S1"
    rejects(
        lambda: run_agent(FakeGemini(), "paid-model", "How many?", [], tools, "CFPB")
    )


def test_real_release():
    tools = AgentTools(
        ROOT,
        dict(
            start_date="2022-11-01",
            end_date="2026-08-31",
            company_name=[],
            product=[],
            sub_product=[],
        ),
    )
    result = tools.query_metrics(**metric_args())
    with duckdb.connect() as con:
        expected = con.execute(
            "SELECT SUM(complaint_count) FROM read_parquet(?)",
            [str(ROOT / FILES["overview"])],
        ).fetchone()[0]
    assert result["rows"][0]["complaint_count"] == expected
    for dataset in ["issues", "geography", "channels"]:
        assert (
            tools.query_metrics(**metric_args(dataset=dataset))["rows"][0][
                "complaint_count"
            ]
            == expected
        )


def test_app():
    from streamlit.testing.v1 import AppTest

    with patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "", "AI_ACCESS_CODE": "", "AI_FREE_TIER_CONFIRMED": ""},
    ):
        app = AppTest.from_file(
            str(ROOT / "dashboard/app.py"), default_timeout=120
        ).run()
        assert not app.exception, app.exception
        assert len(app.tabs) == 8 and app.tabs[-1].label == "AI Analyst"
        assert app.chat_input(key="ai_question").disabled
        assert any("ready for activation" in item.value for item in app.info)
    with patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-offline-only",
            "AI_ACCESS_CODE": "test-workspace",
            "AI_FREE_TIER_CONFIRMED": "true",
        },
    ):
        app = AppTest.from_file(
            str(ROOT / "dashboard/app.py"), default_timeout=120
        ).run()
        assert not app.exception, app.exception
        app.text_input(key="ai_access_entry").set_value("wrong")
        next(
            button for button in app.button if button.label == "Open AI workspace"
        ).click().run()
        assert app.error
        app.text_input(key="ai_access_entry").set_value("test-workspace")
        next(
            button for button in app.button if button.label == "Open AI workspace"
        ).click().run()
        assert not app.exception, app.exception
        assert not app.chat_input(key="ai_question").disabled
        with duckdb.connect() as con:
            total = con.execute(
                "SELECT SUM(complaint_count) FROM read_parquet(?)",
                [str(ROOT / FILES["overview"])],
            ).fetchone()[0]
        with patch("google.genai.Client", return_value=FakeGemini(expected=total)):
            app.chat_input(key="ai_question").set_value(
                "How many complaints are in this selection?"
            ).run()
        assert not app.exception, app.exception
        assert (
            app.session_state["ai_messages"][-1]["result"]["sources"][0]["result"][
                "rows"
            ][0]["complaint_count"]
            == total
        )
        app.session_state["ai_messages"] = [{"role": "user", "content": "old filters"}]
        app.sidebar.multiselect[1].set_value(["Mortgage"]).run()
        assert not app.exception, app.exception
        assert not app.session_state["ai_messages"]


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp:
        tools = fixture(Path(temp))
        test_queries(tools)
        test_loop(tools)
        test_sdk_transport(tools)
        test_evidence(tools)
    test_real_release()
    if "--app" in sys.argv:
        test_app()
    print(
        "AI SQL accounting, filtering, grain isolation, injection, evidence, SDK protocol and citation tests passed (offline; no API key used)."
    )
