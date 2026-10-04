SELECT *,
    md5(CAST(to_json(list_value(company_name)) AS VARCHAR)) AS company_id,
    md5(CAST(to_json(list_value(product, sub_product)) AS VARCHAR)) AS product_category_id,
    md5(CAST(to_json(list_value(product, sub_product, issue, sub_issue)) AS VARCHAR)) AS issue_category_id,
    md5(CAST(to_json(list_value(submission_channel)) AS VARCHAR)) AS submission_channel_id
FROM {{ ref('stg_complaints') }}
