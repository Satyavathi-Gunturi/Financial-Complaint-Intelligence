{{ config(materialized='table', schema='star') }}

SELECT DISTINCT
    md5(CAST(to_json(list_value(state, zip_code)) AS VARCHAR)) AS geography_id,
    state,
    zip_code
FROM {{ ref('complaint_metrics') }}
