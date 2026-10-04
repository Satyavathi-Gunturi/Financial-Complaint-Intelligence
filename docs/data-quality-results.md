# Observed data quality and build results

Results supplied from the executed Colab notebook on 2026-10-04. The public notebook has execution outputs removed; these reports retain the non-sensitive observed counts. These figures are full-data Colab results, not a claim that the full dataset was reprocessed during repository packaging.

## Overall
14,482,997 rows and distinct nonempty IDs; zero duplicate IDs; zero missing IDs; zero missing/unparsed received dates. Received-date range: 2022-11-01–2026-08-31. Nonblank narratives: 2,711,935 (18.72%).

## Yearly coverage
| Year | Complaints | Narratives | Coverage (%) |
|---|---:|---:|---:|
| 2022 | 162,184 | 66,696 | 41.12 |
| 2023 | 1,292,049 | 487,410 | 37.72 |
| 2024 | 2,734,269 | 814,385 | 29.78 |
| 2025 | 5,442,964 | 1,222,050 | 22.45 |
| 2026 | 4,851,531 | 121,394 | 2.50 |

2022 and 2026 are partial years. These percentages must accompany narrative analyses; no cause is asserted for the reduction.

## Missing values
Company 0; product 0; sub-product 5; issue 6; sub-issue 256,750; state 23,438; ZIP 2,434; tags 14,028,161; submission channel 0; sent date 0; public response 6,145,890; response outcome 19; timeliness 0.

## Reconciliation
Silver, wide gold and star builds reported dbt exit code 0. Each retains 14,482,997 complaints. Silver narratives and gold narrative view retain 2,711,935 rows. Timely 14,423,232 + not timely 59,765 = known timeliness 14,482,997. Missing response outcomes: 19. Two tags produce 484,025 unique complaint/tag pairs.

The star/wide reconciliation test compares row counts and sums of every metric flag. It is not an AI answer evaluation. Exact historical dbt test-count logs are not versioned here, so no numeric test total is claimed.

## Repository packaging validation
A separate synthetic smoke build ran successfully while packaging the repository: 17 table models, 4 view models and 126 data tests passed. Additional assertions checked narrative counts, two-tag relationships, leading-zero ZIP preservation, unusual date order and an ISO year boundary. This does not replace or re-run the full-data Colab results above. `scripts/smoke_test.py` reproduces this check; GitHub Actions is configured to run it on pushes and pull requests.
