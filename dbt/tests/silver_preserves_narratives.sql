-- Data test: return violating rows; zero rows means the assertion passes.
select 'narrative_count_mismatch' as failure
where
    (select count(*) from {{ ref('complaint_narratives') }})
    <> (select count(*) from {{ ref('stg_complaints') }} where narrative is not null)
