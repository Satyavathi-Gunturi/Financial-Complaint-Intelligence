-- Grain: one product/sub-product combination. Optional sub-product labels remain NULL.
select distinct product_category_id, product, sub_product
from {{ ref('stg_complaints_keyed') }}
