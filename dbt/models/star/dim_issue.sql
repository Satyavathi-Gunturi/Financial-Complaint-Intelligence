{{ config(materialized='table', schema='star') }}

SELECT
    i.issue_category_id,
    p.product AS issue_product,
    p.sub_product AS issue_sub_product,
    i.issue,
    i.sub_issue
FROM {{ ref('issue_categories') }} i
JOIN {{ ref('product_categories') }} p
    ON i.product_category_id = p.product_category_id
