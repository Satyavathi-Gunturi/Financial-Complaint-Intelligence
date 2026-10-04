SELECT
    NULLIF(TRIM("Complaint ID"), '') AS complaint_id,
    NULLIF(TRIM("Company"), '') AS company_name,
    NULLIF(TRIM("Product"), '') AS product,
    NULLIF(TRIM("Sub-product"), '') AS sub_product,
    NULLIF(TRIM("Issue"), '') AS issue,
    NULLIF(TRIM("Sub-issue"), '') AS sub_issue,
    NULLIF(TRIM("State"), '') AS state,
    NULLIF(TRIM("ZIP code"), '') AS zip_code,
    NULLIF(TRIM("Tags"), '') AS tags_raw,
    NULLIF(TRIM("Submitted via"), '') AS submission_channel,
    NULLIF(TRIM("Company public response"), '') AS company_public_response,
    NULLIF(TRIM("Company response to consumer"), '') AS company_response,
    
    COALESCE(
        TRY_CAST("Date received" AS DATE),
        CAST(TRY_STRPTIME("Date received", '%m/%d/%Y') AS DATE)
    ) AS date_received
    ,
    
    COALESCE(
        TRY_CAST("Date sent to company" AS DATE),
        CAST(TRY_STRPTIME("Date sent to company", '%m/%d/%Y') AS DATE)
    ) AS date_sent_to_company
    ,
    
    CASE
        WHEN "Timely response?" = 'Yes' THEN TRUE
        WHEN "Timely response?" = 'No' THEN FALSE
        ELSE NULL
    END AS timely_response
    ,
    
    CASE
        WHEN COALESCE(TRIM("Consumer complaint narrative"), '') = ''
        THEN NULL
        ELSE "Consumer complaint narrative"
    END AS narrative
    ,
    "Date sent to company" AS date_sent_raw,
    "Timely response?" AS timely_response_raw,
    _source_archive,
    _source_csv,
    _source_record_number,
    _ingested_at
FROM {{ source('bronze', 'bronze_complaints') }}
