{{ config(materialized='table', schema='star') }}

SELECT
    complaint_id,
    company_id,
    product_category_id,
    issue_category_id,
    submission_channel_id,
    md5(CAST(to_json(list_value(state, zip_code)) AS VARCHAR)) AS geography_id,
    md5(CAST(to_json(list_value(company_response, company_public_response, CAST(timely_response AS VARCHAR))) AS VARCHAR)) AS response_id,
    CAST(STRFTIME(date_received, '%Y%m%d') AS INTEGER)
        AS received_date_key,
    CAST(STRFTIME(date_sent_to_company, '%Y%m%d') AS INTEGER)
        AS sent_date_key,
    days_to_send_to_company,
    complaint_count, timely_response_count, not_timely_response_count, known_timeliness_count, unknown_timeliness_count, narrative_count, closed_with_explanation_count, monetary_relief_count, non_monetary_relief_count, in_progress_count, untimely_response_outcome_count, unknown_response_outcome_count, public_response_available_count, missing_state_count, missing_zip_count, missing_issue_count, missing_sub_issue_count, sent_before_received_count
FROM {{ ref('complaint_metrics') }}
