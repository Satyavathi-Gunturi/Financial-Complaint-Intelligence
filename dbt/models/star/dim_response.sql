{{ config(materialized='table', schema='star') }}

SELECT DISTINCT
    md5(CAST(to_json(list_value(company_response, company_public_response, CAST(timely_response AS VARCHAR))) AS VARCHAR)) AS response_id,
    company_response,
    company_public_response,
    timely_response
FROM {{ ref('complaint_metrics') }}
