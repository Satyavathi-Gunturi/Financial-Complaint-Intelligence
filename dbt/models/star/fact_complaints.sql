-- Grain: one complaint. Reuse existing gold flags exactly so wide/star query
-- benchmarks share metric definitions.
{{ config(materialized='table', schema='star') }}

select
    complaint_id,
    company_id,
    product_category_id,
    issue_category_id,
    submission_channel_id,
    md5(cast(to_json(list_value(state, zip_code)) as varchar)) as geography_id,
    md5(
        cast(
            to_json(
                list_value(
                    company_response,
                    company_public_response,
                    cast(timely_response as varchar)
                )
            ) as varchar
        )
    ) as response_id,
    cast(strftime(date_received, '%Y%m%d') as integer) as received_date_key,
    cast(strftime(date_sent_to_company, '%Y%m%d') as integer) as sent_date_key,
    days_to_send_to_company,
    complaint_count,
    timely_response_count,
    not_timely_response_count,
    known_timeliness_count,
    unknown_timeliness_count,
    narrative_count,
    closed_with_explanation_count,
    monetary_relief_count,
    non_monetary_relief_count,
    in_progress_count,
    untimely_response_outcome_count,
    unknown_response_outcome_count,
    public_response_available_count,
    missing_state_count,
    missing_zip_count,
    missing_issue_count,
    missing_sub_issue_count,
    sent_before_received_count
from {{ ref('complaint_metrics') }}
