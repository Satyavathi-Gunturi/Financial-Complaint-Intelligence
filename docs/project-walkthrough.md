# Project walkthrough: what we did and why

This document records the completed development process, not a claim that the AI app is deployed. The data pipeline was executed in Colab on 2026-10-04.

| Step | What we did | Why it was needed | Relevance to our use case |
|---|---|---|---|
| 1. Define the business need | Chose financial complaint intelligence for leadership, with an interactive data agent as the central AI feature | A useful project starts with decisions and users, not tools | Leadership can explore changes, priorities and supporting customer experiences |
| 2. Establish constraints | Used remote Colab compute for an iPad workflow and targeted free services without credit-card requirements | The device cannot practically process this dataset locally | Makes development accessible while leaving hosting choices explicit |
| 3. Acquire real source data | Downloaded official CFPB complaint archives manually | Earlier programmatic download requests returned HTTP 403; manual download provided actual records | Supports a reproducible public-data project rather than toy practice data |
| 4. Inspect the original export | Found the separate bulk export lacked the narrative column | Numeric analytics alone would not support complaint-text retrieval | Motivated selecting the official narratives archive |
| 5. Inventory archives | Inspected ZIP members, field counts, sizes and narrative-column presence | File names alone cannot establish suitability | Confirmed which exports could support both metrics and evidence search |
| 6. Select distinct source files | Retained 18 archive periods, skipped an August duplicate and excluded the narrative-free bulk export | Prevent duplicate ingestion and incompatible-source mixing | Full selected complaint coverage without sampling |
| 7. Convert CSV to bronze Parquet | Read 50,000-row chunks, preserved strings and wrote 299 compressed parts | Bound memory usage and create efficient columnar inputs | Processes every selected complaint without loading the entire CSV collection into memory |
| 8. Add provenance | Added source archive/member, logical record number and ingestion timestamp | Derived answers need traceable source records | Future complaint citations and debugging can point back to source data |
| 9. Verify conversion | Compared written Parquet row counts against CSV reads | Successful file writes alone do not prove completeness | Established 14,482,997 bronze records |
| 10. Save checkpoints | Copied bronze, reports, dbt code and later database snapshots to Drive | Colab temporary storage can disappear after reset | Protects completed work; Drive is not intended as the deployed data service |
| 11. Profile all records | Checked dates, missing IDs, duplicate IDs and yearly narrative coverage | Modeling requires measured data properties | Verified unique complaint IDs and revealed the strong narrative-coverage decline |
| 12. Check categories and missing fields | Inspected response values, channels and comma-separated tags | Avoid invented categories and incorrect missing-value handling | Established two tags, five channels and valid response/timeliness rules |
| 13. Build dbt staging | Standardized column names, parsed dates, mapped timeliness and changed optional blanks to NULL | Transformations should be explicit, reusable and testable | Provides consistent inputs for every downstream metric |
| 14. Build normalized silver | Created complaints, companies, product/issue categories, channels, narratives, tags and tag links | Separate repeated labels and represent real relationships | Supports company/product/issue analysis and evidence retrieval without arbitrary table splitting |
| 15. Test silver | Tested keys, relationships, record preservation, tag uniqueness and product/issue consistency | Joins and transformations can introduce loss or multiplication | Preserved 14,482,997 complaints and 2,711,935 narratives |
| 16. Define metric flags | Added integer counts for timeliness, outcomes, narratives and data-quality conditions | Rates require explicit numerators and denominators | The agent can aggregate correctly across daily, weekly, monthly or custom periods |
| 17. Build wide gold | Joined useful business context at one row per complaint; added a narrative search view | Simple query interfaces reduce repeated joins | Flexible dashboard filters and future read-only agent queries |
| 18. Test wide gold | Checked binary flags, outcome partitions, counts and narrative preservation | A business-ready table still needs correctness checks | Prevents misleading metrics and duplicate complaints |
| 19. Add a star schema alongside gold | Created a complaint fact and seven dimensions in main_star | Showcase dimensional modeling without replacing completed work | Enables a controlled comparison of agent queries on wide versus star representations |
| 20. Reconcile star and wide | Tested foreign keys, unique fact IDs, row counts and every flag total | Benchmark structures must describe the same facts | The star fact retains 14,482,997 rows with matching metric totals |
| 21. Package work in GitHub | Extracted SQL/tests, added documentation, ER diagrams, source information and observed reports | A portfolio needs reviewable implementation and repeatable setup | Reviewers can inspect design choices and distinguish implemented work from roadmap items |

## Why this is medallion plus star
Bronze preserves the selected source records. Silver cleans and organizes them. Gold prepares business metrics in two forms: an existing wide model and an additional dimensional star. Medallion describes the progression; the star describes one gold layout.

## Why we did not pre-aggregate everything by month
The future agent should answer daily, weekly, monthly and custom-period questions. Complaint-level gold preserves that flexibility. SQL will aggregate metric flags for the requested period and calculate rates from summed counts. Summary tables can be introduced later if performance measurements justify them.

## Why the data foundation comes before the AI
An LLM cannot repair undefined metrics, lost records or double-counting joins. Tested data and documented business definitions give the agent reliable tools and provide ground truth for evaluating its answers.

## What is still ahead
Resolve the automated source-download HTTP 403 and accept the first full rolling release; select permanent detailed-data storage; implement the read-only SQL tool, narrative indexing, LLM integration, wide/star benchmarks and operational monitoring. Current narrative_search_documents is a relational view, not semantic search. Checkpoints are development recovery aids, not deployment.

## Updates through 2026-10-05
Recovered a silver-only database backup, rebuilt gold and star successfully, reconciled 14,482,997 rows across all three layers, and saved `complaints_complete.duckdb` (5.13 GB). Exported four independently reconciled dashboard aggregates and deployed six executive tabs in Streamlit, with compact K/M/B counts and consistent hover labels. Implemented a daily, source-hashed rolling 36-month rebuild and branch/PR/merge publication. Synthetic integration validation passes; the first hosted full archive download returned HTTP 403 and published no replacement data. The AI agent remains planned.
