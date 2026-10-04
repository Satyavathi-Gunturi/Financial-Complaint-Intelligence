-- Grain: one issue combination in product context. Flatten product attributes to
-- avoid dimension-to-dimension joins.
{{ config(materialized='table', schema='star') }}

select
    i.issue_category_id,
    p.product as issue_product,
    p.sub_product as issue_sub_product,
    i.issue,
    i.sub_issue
from {{ ref('issue_categories') }} i
join {{ ref('product_categories') }} p on i.product_category_id = p.product_category_id
