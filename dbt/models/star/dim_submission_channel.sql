{{ config(materialized='table', schema='star') }}

SELECT submission_channel_id, submission_channel
FROM {{ ref('submission_channels') }}
