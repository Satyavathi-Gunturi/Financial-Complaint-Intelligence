SELECT 'complaint_count_mismatch' AS failure
WHERE
    (SELECT COUNT(*) FROM {{ ref('complaint_metrics') }})
    <>
    (SELECT COUNT(*) FROM {{ ref('complaints') }})
