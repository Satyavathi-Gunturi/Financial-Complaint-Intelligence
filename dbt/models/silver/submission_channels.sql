-- Grain: one submission method. Shared lookup for complaint relationships.
select distinct submission_channel_id, submission_channel
from {{ ref('stg_complaints_keyed') }}
