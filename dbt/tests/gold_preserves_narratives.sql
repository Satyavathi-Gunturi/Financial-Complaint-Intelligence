-- Data test: return violating rows; zero rows means the assertion passes.
select 'narrative_count_mismatch' as failure
where
    (select count(*) from {{ ref('narrative_search_documents') }})
    <> (select count(*) from {{ ref('complaint_narratives') }})
