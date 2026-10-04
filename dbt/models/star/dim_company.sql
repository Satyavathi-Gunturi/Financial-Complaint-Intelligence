-- Grain: one source company label. Connect directly to the star fact.
{{ config(materialized='table', schema='star') }}

select company_id, company_name
from {{ ref('companies') }}
