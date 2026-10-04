-- Grain: one complaint. Retain every staged record and source provenance; narrative
-- text is stored separately.
select
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
    narrative is not null as has_narrative,
    _source_archive,
    _source_csv,
    _source_record_number,
    _ingested_at
from {{ ref('stg_complaints_keyed') }}
