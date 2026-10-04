SELECT 'complaint_count_mismatch' AS failure
WHERE
    (SELECT COUNT(*) FROM {{ ref('complaints') }})
    <>
    (SELECT COUNT(*) FROM {{ ref('stg_complaints') }})
