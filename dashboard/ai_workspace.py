"""Whole-dashboard conversational workspace; credentials remain server-side."""

import hashlib
import hmac
import json
import os
import threading
import time
from collections import deque

import pandas as pd
import streamlit as st
from agent_tools import DOCUMENTS, FILES, AgentTools
from ai_agent import DEFAULT_MODEL, run_agent
from provider_errors import provider_diagnostic


def setting(name, default=""):
    value = os.environ.get(name)
    if value is not None:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


@st.cache_resource
def budget():
    return threading.Lock(), deque()


def reserve_request():
    """Deployment-process hourly cap, separate from per-session limits."""
    lock, recent = budget()
    now = time.monotonic()
    with lock:
        while recent and recent[0] < now - 3600:
            recent.popleft()
        if len(recent) >= 60:
            raise ValueError(
                "The AI workspace has reached its hourly request limit. Please try later."
            )
        recent.append(now)


def show_answer(item):
    result = item["result"]
    for section in result["answer"]["sections"]:
        # Model output is plain text; no generated HTML, links, or markdown images.
        st.text(section["text"])
        st.caption("Sources: " + ", ".join(section["source_ids"]))
    if result["answer"]["limitations"]:
        st.caption("Interpretation: " + result["answer"]["limitations"])
    if result["answer"]["next_question"]:
        st.caption("Explore next: " + result["answer"]["next_question"])
    with st.expander("Sources, executed SQL and exact results"):
        for source in result["sources"]:
            st.markdown(f"**{source['source_id']} · {source['tool']}**")
            data = source["result"]
            if "sql" in data:
                st.code(data["sql"], language="sql")
                st.json({"parameters": data["parameters"]})
            if "rows" in data:
                if data["rows"]:
                    st.dataframe(
                        pd.DataFrame(data["rows"]), hide_index=True, width="stretch"
                    )
                else:
                    st.caption("No matching rows.")
            if data.get("truncated"):
                st.caption(
                    "Result rows were truncated; the displayed ranking is not a complete distribution."
                )
            if "document" in data:
                st.markdown(f"[Read {data['document']}]({data['url']})")
            if "notes" in data:
                st.caption(data["notes"])
        st.caption(
            f"Model: {result['model']} · Input tokens: {result['input_tokens']:,} · Output tokens: {result['output_tokens']:,}"
        )
        st.download_button(
            "Download answer and query evidence",
            json.dumps(result, indent=2, default=str),
            "complaint_intelligence_answer.json",
            "application/json",
            key=f"ai_download_{item['id']}",
        )


def render(root, scope):
    st.subheader("Ask Financial Complaint Intelligence")
    st.caption("An evidence-backed business analyst across the entire dashboard.")
    cards = st.columns(3)
    for column, title, text in zip(
        cards,
        ["Explore the data", "Understand the business", "Trace every answer"],
        [
            "Ask about demand, companies, issues, outcomes, locations and channels.",
            "Explain reporting terms, metric denominators and CFPB source context.",
            "Review the executed SQL, exact values, documents and complaint IDs.",
        ],
    ):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(text)
    st.caption(
        f"Scope: {scope['start_date']}–{scope['end_date']} · Sidebar company/product/sub-product filters apply. Local chart drilldowns do not apply."
    )
    identities = {
        key: (path.stat().st_mtime_ns, path.stat().st_size)
        for key, filename in FILES.items()
        if (path := root / filename).exists()
    }
    docs_hash = hashlib.sha256(
        "".join(
            (root / filename).read_text() for filename in DOCUMENTS.values()
        ).encode()
    ).hexdigest()
    signature = hashlib.sha256(
        json.dumps([scope, identities, docs_hash], sort_keys=True).encode()
    ).hexdigest()
    if st.session_state.get("ai_scope") != signature:
        st.session_state.ai_scope = signature
        st.session_state.ai_messages = []
        st.session_state.pop("ai_pending", None)
    api_key, access_code = setting("GEMINI_API_KEY"), setting("AI_ACCESS_CODE")
    model = setting("GEMINI_MODEL", DEFAULT_MODEL)
    if (
        not api_key
        or not access_code
        or setting("AI_FREE_TIER_CONFIRMED").lower() != "true"
    ):
        st.info(
            "The AI workspace is ready for activation. The app owner needs a Gemini Free Tier key, a workspace code and free-tier confirmation in Streamlit secrets."
        )
        with st.expander("Owner setup"):
            st.code(
                'GEMINI_API_KEY = "your-free-tier-api-key"\nGEMINI_MODEL = "gemini-2.5-flash"\nAI_FREE_TIER_CONFIRMED = true\nAI_ACCESS_CODE = "a-long-private-workspace-code"',
                language="toml",
            )
            st.markdown(
                "[Activation and operating guide](https://github.com/Satyavathi-Gunturi/Financial-Complaint-Intelligence/blob/main/docs/ai-assistant.md)"
            )
        st.chat_input("AI configuration required", disabled=True, key="ai_question")
        return
    unlock_signature = hashlib.sha256(access_code.encode()).hexdigest()
    if st.session_state.get("ai_unlocked") != unlock_signature:
        with st.form("ai_unlock"):
            entered = st.text_input(
                "Workspace access code", type="password", key="ai_access_entry"
            )
            unlock = st.form_submit_button("Open AI workspace")
        if unlock:
            if hmac.compare_digest(entered.encode(), access_code.encode()):
                st.session_state.ai_unlocked = unlock_signature
                st.rerun()
            else:
                st.error("The workspace code did not match.")
        st.caption(
            "An access code limits use of this API-backed workspace on the public dashboard."
        )
        return
    st.caption(
        "Questions, business context and bounded query/evidence results are sent to Gemini when you submit. Public excerpts have limited masking; AI interpretations require review."
    )
    examples = [
        "Which five companies have the most complaints, and what are their timely response rates?",
        "How has complaint volume changed by month?",
        "What does monetary relief mean, and where does this data come from?",
    ]
    with st.expander("Questions you can ask"):
        for index, example in enumerate(examples):
            if st.button(example, key=f"ai_example_{index}"):
                st.session_state.ai_pending = example
    if st.button("New conversation", key="ai_clear"):
        st.session_state.ai_messages = []
        st.session_state.pop("ai_pending", None)
    for item in st.session_state.ai_messages:
        with st.chat_message(item["role"]):
            if item["role"] == "user":
                st.text(item["content"])
            else:
                show_answer(item)
    question = st.chat_input(
        "Ask about the selected complaint data or business definitions…",
        key="ai_question",
        max_chars=1000,
    )
    question = question or st.session_state.pop("ai_pending", None)
    if not question:
        return
    if st.session_state.get("ai_requests", 0) >= 20:
        st.info("This session has reached its 20-question limit.")
        return
    if time.monotonic() - st.session_state.get("ai_last_request", 0) < 10:
        st.info("Please wait a few seconds before submitting another question.")
        return
    try:
        reserve_request()
    except ValueError as exc:
        st.info(str(exc))
        return
    st.session_state.ai_requests = st.session_state.get("ai_requests", 0) + 1
    st.session_state.ai_last_request = time.monotonic()
    history = []
    for item in st.session_state.ai_messages[-6:]:
        content = item.get("content") or "\n".join(
            s["text"] for s in item["result"]["answer"]["sections"]
        )
        history.append({"role": item["role"], "content": content})
    st.session_state.ai_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.text(question)
    try:
        from google import genai
        from google.genai import types

        tools = AgentTools(root, scope)
        context = (root / DOCUMENTS["business_glossary"]).read_text()
        with (
            st.chat_message("assistant"),
            st.spinner("Checking business context and querying the selected data…"),
        ):
            with genai.Client(
                api_key=api_key,
                vertexai=False,
                http_options=types.HttpOptions(
                    timeout=20000, retry_options=types.HttpRetryOptions(attempts=1)
                ),
            ) as client:
                result = run_agent(client, model, question, history, tools, context)
            item = {
                "role": "assistant",
                "result": result,
                "id": st.session_state.ai_requests,
            }
            show_answer(item)
        st.session_state.ai_messages.append(item)
        st.session_state.ai_messages = st.session_state.ai_messages[-12:]
    except ValueError as exc:
        st.warning(str(exc))
    except Exception as exc:
        diagnostic, action = provider_diagnostic(exc)
        st.error(f"{diagnostic}: {action}")
        st.caption(
            "No supported answer was produced. The dashboard remains available. Provider details and credentials are not displayed; there is no paid fallback."
        )
