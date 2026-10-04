-- Grain: one outcome/public-response/timeliness combination. This is a snapshot
-- category, not response history.
{{ config(materialized='table', schema='star') }}

select distinct
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
    company_response,
    company_public_response,
    timely_response
from {{ ref('complaint_metrics') }}
