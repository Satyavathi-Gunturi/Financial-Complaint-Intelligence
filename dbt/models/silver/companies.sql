SELECT DISTINCT company_id, company_name
        FROM {{ ref('stg_complaints_keyed') }}
