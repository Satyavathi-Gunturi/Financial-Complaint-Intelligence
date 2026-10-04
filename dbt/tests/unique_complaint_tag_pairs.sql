SELECT complaint_id, tag_id
FROM {{ ref('complaint_tags') }}
GROUP BY complaint_id, tag_id
HAVING COUNT(*) > 1
