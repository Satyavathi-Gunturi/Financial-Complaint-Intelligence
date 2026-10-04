-- Data test: return violating rows; zero rows means the assertion passes.
select complaint_id
from {{ ref('complaint_metrics') }}
where
    timely_response_count + not_timely_response_count <> known_timeliness_count
    or known_timeliness_count + unknown_timeliness_count <> 1
    or narrative_count <> case when has_narrative then 1 else 0 end
    or closed_with_explanation_count
    + monetary_relief_count
    + non_monetary_relief_count
    + in_progress_count
    + untimely_response_outcome_count
    + unknown_response_outcome_count
    <> 1
