-- Grain: one narrative-bearing complaint. Keep nonblank narrative text without
-- changing its contents.
select complaint_id, narrative
from {{ ref('stg_complaints') }}
where narrative is not null
