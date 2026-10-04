SELECT 'narrative_count_mismatch' AS failure
WHERE
    (SELECT COUNT(*) FROM {{ ref('narrative_search_documents') }})
    <>
    (SELECT COUNT(*) FROM {{ ref('complaint_narratives') }})
