-- Grain: one submission method. Connect directly to the star fact.
{{ config(materialized='table', schema='star') }}

select submission_channel_id, submission_channel
from {{ ref('submission_channels') }}
