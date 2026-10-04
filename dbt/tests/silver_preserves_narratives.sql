SELECT 'narrative_count_mismatch' AS failure
WHERE
    (SELECT COUNT(*) FROM {{ ref('complaint_narratives') }})
    <>
    (SELECT COUNT(*) FROM {{ ref('stg_complaints') }}
     WHERE narrative IS NOT NULL)
