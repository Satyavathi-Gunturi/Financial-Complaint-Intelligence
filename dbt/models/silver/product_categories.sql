SELECT DISTINCT product_category_id, product, sub_product
        FROM {{ ref('stg_complaints_keyed') }}
