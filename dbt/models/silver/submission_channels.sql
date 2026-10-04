SELECT DISTINCT submission_channel_id, submission_channel
        FROM {{ ref('stg_complaints_keyed') }}
