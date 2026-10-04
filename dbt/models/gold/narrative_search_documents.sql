{{ config(materialized='view') }}

SELECT
    m.complaint_id,
    m.date_received,
    m.company_id,
    m.company_name,
    m.product,
    m.sub_product,
    m.issue,
    m.sub_issue,
    m.state,
    m.company_response,
    m._source_archive,
    m._source_csv,
    n.narrative
FROM {{ ref('complaint_metrics') }} m
JOIN {{ ref('complaint_narratives') }} n
    ON m.complaint_id = n.complaint_id
