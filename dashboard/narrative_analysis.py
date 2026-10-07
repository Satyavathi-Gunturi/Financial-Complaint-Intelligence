"""Local, reproducible topic discovery; no external service or generated claims."""

import re
import warnings

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from threadpoolctl import threadpool_limits

STOP = sorted(
    set(ENGLISH_STOP_WORDS)
    | {
        "xxxx",
        "xx",
        "xxx",
        "xxxxxxxx",
        "complaint",
        "company",
        "consumer",
        "please",
        "said",
        "told",
        "would",
        "cfpb",
        "received",
        "date",
    }
)


def redact(text):
    """Additional limited masking of public excerpts; not a PII guarantee."""
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email]", str(text))
    text = re.sub(r"https?://\S+", "[link]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d ().-]{6,}\d)(?!\w)", "[number]", text)
    return " ".join(text.split())


def discover(frame, topics=6):
    """Assign one strongest learned theme per eligible excerpt, without extrapolation."""
    result = frame.copy()
    vectorizer = TfidfVectorizer(
        stop_words=STOP,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        max_features=4000,
        token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
        sublinear_tf=True,
    )
    try:
        matrix = vectorizer.fit_transform(result["excerpt"].tolist())
    except ValueError:
        return result.assign(topic=-1, weight=0.0), {}
    if min(matrix.shape) < 2:
        return result.assign(topic=-1, weight=0.0), {}
    model = NMF(
        n_components=min(topics, matrix.shape[1], matrix.shape[0] - 1),
        init="nndsvda",
        random_state=42,
        max_iter=300,
    )
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.simplefilter("ignore", ConvergenceWarning)
        weights = model.fit_transform(matrix)
    assigned = weights.argmax(axis=1)
    assigned[weights.sum(axis=1) == 0] = -1
    result["topic"] = assigned
    result["weight"] = weights.max(axis=1)
    words = vectorizer.get_feature_names_out()
    labels = {
        topic: " · ".join(words[np.argsort(component)[-4:][::-1]])
        for topic, component in enumerate(model.components_)
    }
    return result, labels


def theme_summary(assigned, labels):
    """Shares include unassigned excerpts in the denominator."""
    current = assigned[assigned["period"] == "Selected"]
    previous = assigned[assigned["period"] == "Previous"]
    rows = []
    for topic, label in labels.items():
        count = int((current["topic"] == topic).sum())
        if not count:
            continue
        before = int((previous["topic"] == topic).sum())
        share = 100 * count / len(current) if len(current) else 0
        # Small supports suppress unstable comparisons; this is not significance testing.
        change = (
            share - 100 * before / len(previous)
            if len(current) >= 50
            and len(previous) >= 50
            and count >= 10
            and before >= 10
            else None
        )
        rows.append(
            dict(
                topic=topic,
                theme=label,
                narratives=count,
                share_pct=share,
                change_pp=change,
            )
        )
    return pd.DataFrame(
        rows, columns=["topic", "theme", "narratives", "share_pct", "change_pp"]
    ).sort_values("narratives", ascending=False)
