-- Grain: one complaint. Join descriptive context and expose additive metric flags for
-- flexible aggregation.
select
    c.complaint_id,
    c.company_id,
    c.product_category_id,
    c.issue_category_id,
    c.submission_channel_id,
    c.date_received,
    c.date_sent_to_company,
    c.state,
    c.zip_code,
    c.company_public_response,
    c.company_response,
    c.timely_response,
    c.has_narrative,
    c._source_archive,
    c._source_csv,
    c._source_record_number,
    c._ingested_at,
    co.company_name,
    p.product,
    p.sub_product,
    i.issue,
    i.sub_issue,
    ch.submission_channel,
    1 as complaint_count,
    date_diff(
        'day', c.date_received, c.date_sent_to_company
    ) as days_to_send_to_company,
    case when c.timely_response is true then 1 else 0 end as timely_response_count,
    case when c.timely_response is false then 1 else 0 end as not_timely_response_count,
    case when c.timely_response is not null then 1 else 0 end as known_timeliness_count,
    case when c.timely_response is null then 1 else 0 end as unknown_timeliness_count,
    case when c.has_narrative then 1 else 0 end as narrative_count,
    case
        when c.company_response = 'Closed with explanation' then 1 else 0
    end as closed_with_explanation_count,
    case
        when c.company_response = 'Closed with monetary relief' then 1 else 0
    end as monetary_relief_count,
    case
        when c.company_response = 'Closed with non-monetary relief' then 1 else 0
    end as non_monetary_relief_count,
    case when c.company_response = 'In progress' then 1 else 0 end as in_progress_count,
    case
        when c.company_response = 'Untimely response' then 1 else 0
    end as untimely_response_outcome_count,
    case
        when c.company_response is null then 1 else 0
    end as unknown_response_outcome_count,
    case
        when c.company_public_response is not null then 1 else 0
    end as public_response_available_count,
    case when c.state is null then 1 else 0 end as missing_state_count,
    case when c.zip_code is null then 1 else 0 end as missing_zip_count,
    case when i.issue is null then 1 else 0 end as missing_issue_count,
    case when i.sub_issue is null then 1 else 0 end as missing_sub_issue_count,
    case
        when c.date_sent_to_company < c.date_received then 1 else 0
    end as sent_before_received_count
from {{ ref('complaints') }} c
left join {{ ref('companies') }} co on c.company_id = co.company_id
left join
    {{ ref('product_categories') }} p on c.product_category_id = p.product_category_id
left join {{ ref('issue_categories') }} i on c.issue_category_id = i.issue_category_id
left join
    {{ ref('submission_channels') }} ch
    on c.submission_channel_id = ch.submission_channel_id
