-- Grain: one reported state/ZIP combination. Preserve masked ZIPs and NULL
-- attributes; no geocoding is inferred.
{{ config(materialized='table', schema='star') }}

select distinct
    md5(cast(to_json(list_value(state, zip_code)) as varchar)) as geography_id,
    state,
    zip_code
from {{ ref('complaint_metrics') }}
