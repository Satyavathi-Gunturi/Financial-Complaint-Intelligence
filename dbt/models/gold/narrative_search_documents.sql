-- Grain: one narrative-bearing complaint. Supply evidence context for planned
-- retrieval; this is not a vector index.
{{ config(materialized='view') }}

select
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
from {{ ref('complaint_metrics') }} m
join {{ ref('complaint_narratives') }} n on m.complaint_id = n.complaint_id
