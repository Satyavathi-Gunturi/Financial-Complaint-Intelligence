{{ config(materialized='table', schema='star') }}

SELECT product_category_id, product, sub_product
FROM {{ ref('product_categories') }}
