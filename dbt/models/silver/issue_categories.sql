SELECT DISTINCT
            issue_category_id, product_category_id, issue, sub_issue
        FROM {{ ref('stg_complaints_keyed') }}
