-- Grain: one complaint. Derive stable category keys from JSON-encoded labels,
-- including NULL components.
select
    *,
    md5(cast(to_json(list_value(company_name)) as varchar)) as company_id,
    md5(
        cast(to_json(list_value(product, sub_product)) as varchar)
    ) as product_category_id,
    md5(
        cast(to_json(list_value(product, sub_product, issue, sub_issue)) as varchar)
    ) as issue_category_id,
    md5(
        cast(to_json(list_value(submission_channel)) as varchar)
    ) as submission_channel_id
from {{ ref('stg_complaints') }}
