SELECT
            complaint_id,
            company_id,
            product_category_id,
            issue_category_id,
            submission_channel_id,
            date_received,
            date_sent_to_company,
            state,
            zip_code,
            company_public_response,
            company_response,
            timely_response,
            narrative IS NOT NULL AS has_narrative,
            _source_archive,
            _source_csv,
            _source_record_number,
            _ingested_at
        FROM {{ ref('stg_complaints_keyed') }}
