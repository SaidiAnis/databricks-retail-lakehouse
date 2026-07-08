-- One row per calendar day spanning the invoice date range in the data.
with bounds as (
    select
        min(date(invoice_at)) as min_date,
        max(date(invoice_at)) as max_date
    from {{ ref('stg_online_retail') }}
),

date_spine as (
    select explode(sequence(min_date, max_date, interval 1 day)) as date_day
    from bounds
)

select
    date_day,
    year(date_day) as year,
    month(date_day) as month,
    date_format(date_day, 'MMMM') as month_name,
    quarter(date_day) as quarter,
    dayofweek(date_day) as day_of_week,
    date_format(date_day, 'EEEE') as day_name,
    dayofweek(date_day) in (1, 7) as is_weekend
from date_spine
