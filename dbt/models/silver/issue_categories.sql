-- Grain: one product-context/issue/sub-issue combination. Preserve taxonomy context
-- for repeated issue labels.
select distinct issue_category_id, product_category_id, issue, sub_issue
from {{ ref('stg_complaints_keyed') }}
