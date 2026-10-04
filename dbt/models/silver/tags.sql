-- Grain: one tag label. Assign stable keys to individual tags, not comma-separated
-- tag combinations.
select distinct md5(cast(to_json(list_value(tag_name)) as varchar)) as tag_id, tag_name
from {{ ref('stg_complaint_tags') }}
