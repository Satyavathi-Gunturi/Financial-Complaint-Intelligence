-- Data test: return violating rows; zero rows means the assertion passes.
select 'row_count_mismatch' as failure
where
    (select count(*) from {{ ref('stg_complaints') }})
    <> (select count(*) from {{ source('bronze', 'bronze_complaints') }})
