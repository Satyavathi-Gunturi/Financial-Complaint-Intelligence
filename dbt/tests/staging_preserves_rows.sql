SELECT 'row_count_mismatch' AS failure
WHERE
    (SELECT COUNT(*) FROM {{ ref('stg_complaints') }})
    <>
    (SELECT COUNT(*) FROM {{ source('bronze', 'bronze_complaints') }})
