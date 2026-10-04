-- Grain: one source complaint. Standardize types and blanks without filtering records.
select
    nullif(trim("Complaint ID"), '') as complaint_id,
    nullif(trim("Company"), '') as company_name,
    nullif(trim("Product"), '') as product,
    nullif(trim("Sub-product"), '') as sub_product,
    nullif(trim("Issue"), '') as issue,
    nullif(trim("Sub-issue"), '') as sub_issue,
    nullif(trim("State"), '') as state,
    nullif(trim("ZIP code"), '') as zip_code,
    nullif(trim("Tags"), '') as tags_raw,
    nullif(trim("Submitted via"), '') as submission_channel,
    nullif(trim("Company public response"), '') as company_public_response,
    nullif(trim("Company response to consumer"), '') as company_response,

    coalesce(
        try_cast("Date received" as date),
        cast(try_strptime("Date received", '%m/%d/%Y') as date)
    ) as date_received,

    coalesce(
        try_cast("Date sent to company" as date),
        cast(try_strptime("Date sent to company", '%m/%d/%Y') as date)
    ) as date_sent_to_company,

    case
        when "Timely response?" = 'Yes'
        then true
        when "Timely response?" = 'No'
        then false
        else null
    end as timely_response,

    case
        when coalesce(trim("Consumer complaint narrative"), '') = ''
        then null
        else "Consumer complaint narrative"
    end as narrative,
    "Date sent to company" as date_sent_raw,
    "Timely response?" as timely_response_raw,
    _source_archive,
    _source_csv,
    _source_record_number,
    _ingested_at
from {{ source('bronze', 'bronze_complaints') }}
