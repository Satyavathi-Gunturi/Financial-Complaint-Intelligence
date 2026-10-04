-- Grain: one product/sub-product combination. Connect directly to the star fact.
{{ config(materialized='table', schema='star') }}

select product_category_id, product, sub_product
from {{ ref('product_categories') }}
