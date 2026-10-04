-- Grain: one complaint/tag pair. Filter this bridge with EXISTS to avoid double
-- counting complaints.
select complaint_id, md5(cast(to_json(list_value(tag_name)) as varchar)) as tag_id
from {{ ref('stg_complaint_tags') }}
