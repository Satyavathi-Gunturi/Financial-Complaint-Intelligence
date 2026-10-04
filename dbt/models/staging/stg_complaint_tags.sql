SELECT DISTINCT
    complaint_id,
    TRIM(tag_value) AS tag_name
FROM {{ ref('stg_complaints') }},
    UNNEST(string_split(tags_raw, ',')) AS tag_values(tag_value)
WHERE NULLIF(TRIM(tag_value), '') IS NOT NULL
