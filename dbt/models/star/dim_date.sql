{{ config(materialized='table', schema='star') }}

WITH bounds AS (
    SELECT
        LEAST(
            MIN(date_received), MIN(date_sent_to_company)
        ) AS first_date,
        GREATEST(
            MAX(date_received), MAX(date_sent_to_company)
        ) AS last_date
    FROM {{ ref('complaint_metrics') }}
),
calendar AS (
    SELECT CAST(day_value AS DATE) AS calendar_date
    FROM bounds,
    LATERAL generate_series(
        first_date, last_date, INTERVAL '1 day'
    ) AS days(day_value)
)
SELECT
    CAST(STRFTIME(calendar_date, '%Y%m%d') AS INTEGER) AS date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date)::INTEGER AS year,
    EXTRACT(QUARTER FROM calendar_date)::INTEGER AS quarter,
    EXTRACT(MONTH FROM calendar_date)::INTEGER AS month,
    STRFTIME(calendar_date, '%B') AS month_name,
    CAST(DATE_TRUNC('month', calendar_date) AS DATE) AS month_start,
    CAST(DATE_TRUNC('week', calendar_date) AS DATE) AS week_start,
    EXTRACT(ISOYEAR FROM calendar_date)::INTEGER AS iso_year,
    EXTRACT(WEEK FROM calendar_date)::INTEGER AS iso_week,
    EXTRACT(ISODOW FROM calendar_date)::INTEGER AS weekday_number,
    STRFTIME(calendar_date, '%A') AS weekday_name,
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7) AS is_weekend
FROM calendar
