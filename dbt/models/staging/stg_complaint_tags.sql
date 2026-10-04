-- Grain: one unique complaint/tag pair. Split multi-valued tags without multiplying
-- the complaint fact.
select distinct complaint_id, trim(tag_value) as tag_name
from
    {{ ref('stg_complaints') }},
    unnest(string_split(tags_raw, ',')) as tag_values(tag_value)
where nullif(trim(tag_value), '') is not null
