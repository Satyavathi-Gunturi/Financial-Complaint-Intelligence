SELECT complaint_id, md5(CAST(to_json(list_value(tag_name)) AS VARCHAR)) AS tag_id
FROM {{ ref('stg_complaint_tags') }}
