SELECT c.complaint_id
FROM {{ ref('complaints') }} c
JOIN {{ ref('issue_categories') }} i
    ON c.issue_category_id = i.issue_category_id
WHERE c.product_category_id <> i.product_category_id
