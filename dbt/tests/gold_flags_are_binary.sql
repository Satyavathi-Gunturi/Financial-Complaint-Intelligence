-- Data test: return violating rows; zero rows means the assertion passes.
select complaint_id
from {{ ref('complaint_metrics') }}
where
    complaint_count <> 1
    or timely_response_count not in (0, 1)
    or not_timely_response_count not in (0, 1)
    or known_timeliness_count not in (0, 1)
    or unknown_timeliness_count not in (0, 1)
    or narrative_count not in (0, 1)
    or closed_with_explanation_count not in (0, 1)
    or monetary_relief_count not in (0, 1)
    or non_monetary_relief_count not in (0, 1)
    or in_progress_count not in (0, 1)
    or untimely_response_outcome_count not in (0, 1)
    or unknown_response_outcome_count not in (0, 1)
    or public_response_available_count not in (0, 1)
    or missing_state_count not in (0, 1)
    or missing_zip_count not in (0, 1)
    or missing_issue_count not in (0, 1)
    or missing_sub_issue_count not in (0, 1)
    or sent_before_received_count not in (0, 1)
