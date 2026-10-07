# Metric definitions

Grain: one complaint. Default time field: received date. Weeks start Monday. All counts are integer flags; aggregate first and calculate rates second.

| Metric | Calculation |
|---|---|
| Complaint volume | `SUM(complaint_count)` |
| Timely response rate (%) | `100.0 * SUM(timely_response_count) / NULLIF(SUM(known_timeliness_count), 0)` |
| Narrative coverage (%) | `100.0 * SUM(narrative_count) / NULLIF(SUM(complaint_count), 0)` |

A zero denominator yields NULL, not a fabricated zero percent. Dates can be grouped daily, weekly, monthly or by custom windows. Use half-open intervals for date filters and flag partial comparison periods. Do not average subgroup rates or count complaint/tag join rows as complaints.

## Flags
| Column | Equals 1 when |
|---|---|
| complaint_count | Always |
| timely_response_count | Source timeliness is true |
| not_timely_response_count | Source timeliness is false |
| known_timeliness_count | Timeliness is non-NULL |
| unknown_timeliness_count | Timeliness is NULL |
| narrative_count | A published nonblank narrative exists |
| closed_with_explanation_count | Outcome is Closed with explanation |
| monetary_relief_count | Outcome is Closed with monetary relief |
| non_monetary_relief_count | Outcome is Closed with non-monetary relief |
| in_progress_count | Outcome is In progress in the export |
| untimely_response_outcome_count | Outcome category is Untimely response |
| unknown_response_outcome_count | Outcome is NULL |
| public_response_available_count | Public response category is present |
| missing_state_count | State is NULL |
| missing_zip_count | ZIP is NULL |
| missing_issue_count | Issue is NULL |
| missing_sub_issue_count | Sub-issue is NULL |
| sent_before_received_count | Sent date precedes received date |

`days_to_send_to_company` is received-to-referral elapsed days, not resolution duration. Public response availability indicates a category, not free-text narrative. Relief flags imply no dollar amount. Missing ZIP/state only describes this published record. Source timeliness and the untimely outcome category are distinct fields; do not substitute one for the other.

`dbt/metric_definitions.yml` records core formulas; gold schema YAML describes every flag. AI Analyst can read this document through its business-document tool. Its allowlisted aggregate expressions mirror the formulas above in `dashboard/agent_tools.py`; tests verify weighted rates, NULL denominators and query accounting.
