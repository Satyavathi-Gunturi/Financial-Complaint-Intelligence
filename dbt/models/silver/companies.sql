-- Grain: one source company label. Preserve source identity rather than inferring
-- corporate mergers.
select distinct company_id, company_name from {{ ref('stg_complaints_keyed') }}
