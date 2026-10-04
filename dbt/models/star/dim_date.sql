-- Grain: one calendar day. Support received and sent date roles, Monday weeks and
-- paired ISO year/week attributes.
{{ config(materialized='table', schema='star') }}

with
    bounds as (
        select
            least(min(date_received), min(date_sent_to_company)) as first_date,
            greatest(max(date_received), max(date_sent_to_company)) as last_date
        from {{ ref('complaint_metrics') }}
    ),
    calendar as (
        select cast(day_value as date) as calendar_date
        from
            bounds,
            lateral generate_series(first_date, last_date, interval '1 day') as days(
                day_value
            )
    )
select
    cast(strftime(calendar_date, '%Y%m%d') as integer) as date_key,
    calendar_date,
    extract(year from calendar_date)::integer as year,
    extract(quarter from calendar_date)::integer as quarter,
    extract(month from calendar_date)::integer as month,
    strftime(calendar_date, '%B') as month_name,
    cast(date_trunc('month', calendar_date) as date) as month_start,
    cast(date_trunc('week', calendar_date) as date) as week_start,
    extract(isoyear from calendar_date)::integer as iso_year,
    extract(week from calendar_date)::integer as iso_week,
    extract(isodow from calendar_date)::integer as weekday_number,
    strftime(calendar_date, '%A') as weekday_name,
    extract(isodow from calendar_date) in (6, 7) as is_weekend
from calendar
