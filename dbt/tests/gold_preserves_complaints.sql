-- Data test: return violating rows; zero rows means the assertion passes.
select 'complaint_count_mismatch' as failure
where
    (select count(*) from {{ ref('complaint_metrics') }})
    <> (select count(*) from {{ ref('complaints') }})
