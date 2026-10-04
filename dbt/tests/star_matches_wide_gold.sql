
WITH star_totals AS (
    SELECT COUNT(*) AS rows, SUM(complaint_count) AS complaint_count,
SUM(timely_response_count) AS timely_response_count,
SUM(not_timely_response_count) AS not_timely_response_count,
SUM(known_timeliness_count) AS known_timeliness_count,
SUM(unknown_timeliness_count) AS unknown_timeliness_count,
SUM(narrative_count) AS narrative_count,
SUM(closed_with_explanation_count) AS closed_with_explanation_count,
SUM(monetary_relief_count) AS monetary_relief_count,
SUM(non_monetary_relief_count) AS non_monetary_relief_count,
SUM(in_progress_count) AS in_progress_count,
SUM(untimely_response_outcome_count) AS untimely_response_outcome_count,
SUM(unknown_response_outcome_count) AS unknown_response_outcome_count,
SUM(public_response_available_count) AS public_response_available_count,
SUM(missing_state_count) AS missing_state_count,
SUM(missing_zip_count) AS missing_zip_count,
SUM(missing_issue_count) AS missing_issue_count,
SUM(missing_sub_issue_count) AS missing_sub_issue_count,
SUM(sent_before_received_count) AS sent_before_received_count
    FROM {{ ref('fact_complaints') }}
),
wide_totals AS (
    SELECT COUNT(*) AS rows, SUM(complaint_count) AS complaint_count,
SUM(timely_response_count) AS timely_response_count,
SUM(not_timely_response_count) AS not_timely_response_count,
SUM(known_timeliness_count) AS known_timeliness_count,
SUM(unknown_timeliness_count) AS unknown_timeliness_count,
SUM(narrative_count) AS narrative_count,
SUM(closed_with_explanation_count) AS closed_with_explanation_count,
SUM(monetary_relief_count) AS monetary_relief_count,
SUM(non_monetary_relief_count) AS non_monetary_relief_count,
SUM(in_progress_count) AS in_progress_count,
SUM(untimely_response_outcome_count) AS untimely_response_outcome_count,
SUM(unknown_response_outcome_count) AS unknown_response_outcome_count,
SUM(public_response_available_count) AS public_response_available_count,
SUM(missing_state_count) AS missing_state_count,
SUM(missing_zip_count) AS missing_zip_count,
SUM(missing_issue_count) AS missing_issue_count,
SUM(missing_sub_issue_count) AS missing_sub_issue_count,
SUM(sent_before_received_count) AS sent_before_received_count
    FROM {{ ref('complaint_metrics') }}
)
SELECT 'star_wide_mismatch' AS failure
FROM star_totals s CROSS JOIN wide_totals w
WHERE s.rows <> w.rows OR s.complaint_count IS DISTINCT FROM w.complaint_count OR s.timely_response_count IS DISTINCT FROM w.timely_response_count OR s.not_timely_response_count IS DISTINCT FROM w.not_timely_response_count OR s.known_timeliness_count IS DISTINCT FROM w.known_timeliness_count OR s.unknown_timeliness_count IS DISTINCT FROM w.unknown_timeliness_count OR s.narrative_count IS DISTINCT FROM w.narrative_count OR s.closed_with_explanation_count IS DISTINCT FROM w.closed_with_explanation_count OR s.monetary_relief_count IS DISTINCT FROM w.monetary_relief_count OR s.non_monetary_relief_count IS DISTINCT FROM w.non_monetary_relief_count OR s.in_progress_count IS DISTINCT FROM w.in_progress_count OR s.untimely_response_outcome_count IS DISTINCT FROM w.untimely_response_outcome_count OR s.unknown_response_outcome_count IS DISTINCT FROM w.unknown_response_outcome_count OR s.public_response_available_count IS DISTINCT FROM w.public_response_available_count OR s.missing_state_count IS DISTINCT FROM w.missing_state_count OR s.missing_zip_count IS DISTINCT FROM w.missing_zip_count OR s.missing_issue_count IS DISTINCT FROM w.missing_issue_count OR s.missing_sub_issue_count IS DISTINCT FROM w.missing_sub_issue_count OR s.sent_before_received_count IS DISTINCT FROM w.sent_before_received_count
