SELECT complaint_id
FROM {{ ref('complaint_metrics') }}
WHERE
    timely_response_count + not_timely_response_count
        <> known_timeliness_count
    OR known_timeliness_count + unknown_timeliness_count <> 1
    OR narrative_count <> CASE WHEN has_narrative THEN 1 ELSE 0 END
    OR closed_with_explanation_count
        + monetary_relief_count
        + non_monetary_relief_count
        + in_progress_count
        + untimely_response_outcome_count
        + unknown_response_outcome_count <> 1
