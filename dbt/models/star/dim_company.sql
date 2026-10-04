{{ config(materialized='table', schema='star') }}

SELECT company_id, company_name
FROM {{ ref('companies') }}
