-- Data test: return violating rows; zero rows means the assertion passes.
with
    star_totals as (
        select
            count(*) as rows,
            sum(complaint_count) as complaint_count,
            sum(timely_response_count) as timely_response_count,
            sum(not_timely_response_count) as not_timely_response_count,
            sum(known_timeliness_count) as known_timeliness_count,
            sum(unknown_timeliness_count) as unknown_timeliness_count,
            sum(narrative_count) as narrative_count,
            sum(closed_with_explanation_count) as closed_with_explanation_count,
            sum(monetary_relief_count) as monetary_relief_count,
            sum(non_monetary_relief_count) as non_monetary_relief_count,
            sum(in_progress_count) as in_progress_count,
            sum(untimely_response_outcome_count) as untimely_response_outcome_count,
            sum(unknown_response_outcome_count) as unknown_response_outcome_count,
            sum(public_response_available_count) as public_response_available_count,
            sum(missing_state_count) as missing_state_count,
            sum(missing_zip_count) as missing_zip_count,
            sum(missing_issue_count) as missing_issue_count,
            sum(missing_sub_issue_count) as missing_sub_issue_count,
            sum(sent_before_received_count) as sent_before_received_count
        from {{ ref('fact_complaints') }}
    ),
    wide_totals as (
        select
            count(*) as rows,
            sum(complaint_count) as complaint_count,
            sum(timely_response_count) as timely_response_count,
            sum(not_timely_response_count) as not_timely_response_count,
            sum(known_timeliness_count) as known_timeliness_count,
            sum(unknown_timeliness_count) as unknown_timeliness_count,
            sum(narrative_count) as narrative_count,
            sum(closed_with_explanation_count) as closed_with_explanation_count,
            sum(monetary_relief_count) as monetary_relief_count,
            sum(non_monetary_relief_count) as non_monetary_relief_count,
            sum(in_progress_count) as in_progress_count,
            sum(untimely_response_outcome_count) as untimely_response_outcome_count,
            sum(unknown_response_outcome_count) as unknown_response_outcome_count,
            sum(public_response_available_count) as public_response_available_count,
            sum(missing_state_count) as missing_state_count,
            sum(missing_zip_count) as missing_zip_count,
            sum(missing_issue_count) as missing_issue_count,
            sum(missing_sub_issue_count) as missing_sub_issue_count,
            sum(sent_before_received_count) as sent_before_received_count
        from {{ ref('complaint_metrics') }}
    )
select 'star_wide_mismatch' as failure
from star_totals s
cross join wide_totals w
where
    s.rows <> w.rows
    or s.complaint_count is distinct from w.complaint_count
    or s.timely_response_count is distinct from w.timely_response_count
    or s.not_timely_response_count is distinct from w.not_timely_response_count
    or s.known_timeliness_count is distinct from w.known_timeliness_count
    or s.unknown_timeliness_count is distinct from w.unknown_timeliness_count
    or s.narrative_count is distinct from w.narrative_count
    or s.closed_with_explanation_count is distinct from w.closed_with_explanation_count
    or s.monetary_relief_count is distinct from w.monetary_relief_count
    or s.non_monetary_relief_count is distinct from w.non_monetary_relief_count
    or s.in_progress_count is distinct from w.in_progress_count
    or s.untimely_response_outcome_count
    is distinct from w.untimely_response_outcome_count
    or s.unknown_response_outcome_count
    is distinct from w.unknown_response_outcome_count
    or s.public_response_available_count
    is distinct from w.public_response_available_count
    or s.missing_state_count is distinct from w.missing_state_count
    or s.missing_zip_count is distinct from w.missing_zip_count
    or s.missing_issue_count is distinct from w.missing_issue_count
    or s.missing_sub_issue_count is distinct from w.missing_sub_issue_count
    or s.sent_before_received_count is distinct from w.sent_before_received_count
