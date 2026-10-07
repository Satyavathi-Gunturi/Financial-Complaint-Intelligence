"""Source-grounded executive issue summaries and verbatim evidence selection."""

import re

import pandas as pd


def issue_summary(assigned):
    frame = assigned.copy()
    frame["concern"] = (
        frame["issue"].fillna("Issue not recorded").replace("", "Issue not recorded")
    )
    current = frame[frame.period == "Selected"]
    previous = frame[frame.period == "Previous"]
    counts = current.concern.value_counts()
    before = previous.concern.value_counts()
    rows = []
    for concern, count in counts.items():
        prior = int(before.get(concern, 0))
        share = 100 * count / len(current)
        change = (
            share - 100 * prior / len(previous)
            if len(current) >= 50
            and len(previous) >= 50
            and count >= 10
            and prior >= 10
            else None
        )
        rows.append(
            dict(
                concern=concern,
                narratives=int(count),
                share_pct=share,
                prior_narratives=prior,
                change_pp=change,
            )
        )
    return frame, pd.DataFrame(rows)


def investigation_question(concern):
    label = concern.lower()
    if "incorrect" in label or "error" in label:
        return "Which information errors recur, and what do customers report about correction attempts?"
    if "improper use" in label or "identity" in label:
        return "What do customers describe about report access, authorization or identity-related disputes?"
    if "investigation" in label or "dispute" in label:
        return "Do customers describe repeated disputes, unclear outcomes or difficulty getting a response?"
    if "payment" in label:
        return "What do customers report about payment processing, fees or account records?"
    if "collection" in label or "debt" in label:
        return "Which collection contacts or disputed-debt experiences recur in the evidence?"
    return "Which repeated customer experiences within this issue warrant a closer process review?"


def representative_quote(text, concern):
    """Choose a readable verbatim sentence; never paraphrase or invent testimony."""
    words = set(re.findall(r"[a-z]{4,}", concern.lower())) - {
        "your",
        "with",
        "from",
        "into",
        "problem",
        "information",
    }
    sentences = re.split(r"(?<=[.!?])\s+", str(text))
    eligible = [
        s
        for s in sentences
        if 40 <= len(s) <= 420 and len(re.findall(r"\b[xX]{2,}\b", s)) < 5
    ]
    if eligible:
        sentence = max(
            eligible,
            key=lambda s: (
                len(words & set(re.findall(r"[a-z]{4,}", s.lower())))
                - 2 * bool(re.search(r"\b(section|usc|u\.s\.c|statute)\b", s, re.I)),
                -sentences.index(s),
            ),
        )
        return sentence
    return str(text)[:300] + ("…" if len(str(text)) > 300 else "")
