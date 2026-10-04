SELECT complaint_id, narrative
        FROM {{ ref('stg_complaints') }}
        WHERE narrative IS NOT NULL
