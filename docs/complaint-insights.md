# Complaint Insights

The seventh dashboard tab analyzes customer-reported narrative excerpts using local unsupervised machine learning: TF–IDF features and non-negative matrix factorization (NMF). No paid API, model download, external text transmission or LLM key is required. The separately configured eighth AI Analyst tab adds whole-dashboard Gemini conversations; [its setup and data-transmission contract](ai-assistant.md) differ from this local-only NLP tab.

## Evidence and filters

`dashboard_narratives.parquet` is a global deterministic MD5 complaint-ID sample of up to 60,000 narrative-bearing complaints. The uploaded historical export contains 60,000 unique IDs, occupies 14.53 MiB, and records a source population of 2,711,935 narratives. This sample is not balanced by company, product, date or issue. Narrow filters may have limited or no evidence. Results never extrapolate sample theme counts to all complaints.

The tab shares received-date, company, product and sub-product filters with the other tabs. State and issue appear as evidence context; existing local issue/geography controls do not filter this tab. Excerpts contain the first 2,000 characters of each narrative. The export additionally masks common email addresses, URLs and long number sequences, with no guarantee of complete anonymization. Names or other personal details may remain. Only previously public CFPB narratives are intended for this public serving export.

An embedded SHA-256 ties the evidence to the exact overview Parquet. The dashboard disables analysis when hashes differ. Export validation reconciles complaint/narrative counts and date bounds against the overview and checks unique IDs. Full source archives and DuckDB checkpoints remain outside the repository.

## Analysis contract

Analysis is explicitly enabled by a toggle. At least 20 matching exported excerpts are required. A deterministic subset of at most 3,000 excerpts per period is selected by MD5 ID ordering. A single model is fitted across the selection and the preceding equal-length date window, with the same company/product/sub-product filters. Comparison is disabled if the entire preceding window falls outside snapshot coverage.

The vectorizer uses English stop words plus selected CFPB boilerplate tokens, one/two-word features, minimum document frequency 2, maximum document frequency 95%, and at most 4,000 features. NMF discovers at most six components using deterministic initialization and seed 42; CPU thread limits bound local resource use. Every usable excerpt is assigned to its strongest component. Zero-vocabulary excerpts remain unassigned. Theme labels display the four largest component terms. Weights are not confidence probabilities; themes may overlap or reflect boilerplate, and labels can change when filters change.

The dashboard provides an executive briefing, six ranked customer-concern cards with K/M/B sample counts and verbatim evidence, supported prior-period share changes, investigation questions and exact-count CSV export. Concern labels/counts use the recorded source issue (including missing issues), independently of NLP cluster assignments. This avoids presenting legal boilerplate word clusters as business problems. Supporting complaint IDs/excerpts are ranked by NLP weight; recurring model terms remain in an expandable analysis panel. Phrase search is literal and applies only to analyzed excerpts in the selected theme; it is not semantic retrieval or a full-corpus search.

Executive concern shares divide by all analyzed selected excerpts, including NLP-unassigned records. Every excerpt contributes once to its recorded issue. Prior-period changes require at least 50 analyzed excerpts per period and at least 10 supporting excerpts for the particular recorded issue in each period. These are sample support guards, not statistical significance tests. No sentiment, financial-loss estimates, verified misconduct or root-cause claims are inferred.

## Export and refresh

From a local copy of the complete checkpoint:

```bash
pip install -r dashboard/requirements.txt
python scripts/export_narrative_sample.py \
  --database /path/to/complaints_complete.duckdb \
  --overview dashboard_daily_company_product.parquet \
  --output dashboard_narratives.parquet
```

For Colab, copy the checkpoint from Drive to `/content` first and save the output back to Drive after verification. Selecting sample IDs from silver before joining gold avoids joining all narrative text into the 14.48-million-row metric table. The exporter keeps a hash-ranked prefix and halves its sample size if necessary to remain below 24 MiB (the browser upload limit is 25 MB). Data publication follows branch → PR → merge; `*.parquet` is ignored by default, so deliberate git uploads need `git add -f`.

The rolling refresh stages the four reconciled aggregate files and the matching narrative evidence file together, records all five hashes in the release manifest, and publishes through one PR. Narrative-export failure prevents publication. The CFPB HTTP 403 limitation still applies; scheduled refresh remains enabled and failed builds retain the last validated release. Current source restrictions do not guarantee new narrative availability.

## Validation

`python scripts/test_narrative_analysis.py` checks distinct synthetic topics, deterministic assignments, count/share accounting, sparse evidence, masking and checkpoint mismatch rejection. `python scripts/test_narrative_analysis.py --app` also exercises the real uploaded sample, evidence search and filtered prior-period dashboard behavior. `python dashboard/check_app.py` verifies existing headline totals, eight tabs and aggregate filters.

Method reference: [scikit-learn topic extraction with TF–IDF and NMF](https://scikit-learn.org/1.8/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html).

## Executive interpretation

The briefing reports the leading recorded issue, top-three issue concentration and the largest supported sample-share increase. The labels come from source categories, not an LLM or manual attribution of all cluster members. Cards include a representative verbatim sentence and complaint ID. Investigation prompts are bounded questions drawn from the recorded issue; they are not inferred causes or verified company failures. Full excerpts and literal phrase search remain available. A supporting word-cluster explorer uses styled phrase clouds with overlapping within-cluster document-mention counts. Phrase size encodes mention frequency rather than model confidence. Cluster selection intersects the selected source issue and literal phrase search for evidence review. Cluster support counts remain separate from source-issue counts.
