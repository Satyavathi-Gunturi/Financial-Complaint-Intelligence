SELECT
    c.*,
    co.company_name,
    p.product,
    p.sub_product,
    i.issue,
    i.sub_issue,
    ch.submission_channel,
    1 AS complaint_count,
    DATE_DIFF(
        'day', c.date_received, c.date_sent_to_company
    ) AS days_to_send_to_company,
    CASE WHEN c.timely_response IS TRUE THEN 1 ELSE 0 END AS timely_response_count,
    CASE WHEN c.timely_response IS FALSE THEN 1 ELSE 0 END AS not_timely_response_count,
    CASE WHEN c.timely_response IS NOT NULL THEN 1 ELSE 0 END AS known_timeliness_count,
    CASE WHEN c.timely_response IS NULL THEN 1 ELSE 0 END AS unknown_timeliness_count,
    CASE WHEN c.has_narrative THEN 1 ELSE 0 END AS narrative_count,
    CASE WHEN c.company_response = 'Closed with explanation' THEN 1 ELSE 0 END AS closed_with_explanation_count,
    CASE WHEN c.company_response = 'Closed with monetary relief' THEN 1 ELSE 0 END AS monetary_relief_count,
    CASE WHEN c.company_response = 'Closed with non-monetary relief' THEN 1 ELSE 0 END AS non_monetary_relief_count,
    CASE WHEN c.company_response = 'In progress' THEN 1 ELSE 0 END AS in_progress_count,
    CASE WHEN c.company_response = 'Untimely response' THEN 1 ELSE 0 END AS untimely_response_outcome_count,
    CASE WHEN c.company_response IS NULL THEN 1 ELSE 0 END AS unknown_response_outcome_count,
    CASE WHEN c.company_public_response IS NOT NULL THEN 1 ELSE 0 END AS public_response_available_count,
    CASE WHEN c.state IS NULL THEN 1 ELSE 0 END AS missing_state_count,
    CASE WHEN c.zip_code IS NULL THEN 1 ELSE 0 END AS missing_zip_count,
    CASE WHEN i.issue IS NULL THEN 1 ELSE 0 END AS missing_issue_count,
    CASE WHEN i.sub_issue IS NULL THEN 1 ELSE 0 END AS missing_sub_issue_count,
    CASE WHEN c.date_sent_to_company < c.date_received THEN 1 ELSE 0 END AS sent_before_received_count
FROM {{ ref('complaints') }} c
LEFT JOIN {{ ref('companies') }} co
    ON c.company_id = co.company_id
LEFT JOIN {{ ref('product_categories') }} p
    ON c.product_category_id = p.product_category_id
LEFT JOIN {{ ref('issue_categories') }} i
    ON c.issue_category_id = i.issue_category_id
LEFT JOIN {{ ref('submission_channels') }} ch
    ON c.submission_channel_id = ch.submission_channel_id
