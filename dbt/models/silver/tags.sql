SELECT DISTINCT md5(CAST(to_json(list_value(tag_name)) AS VARCHAR)) AS tag_id, tag_name
FROM {{ ref('stg_complaint_tags') }}
