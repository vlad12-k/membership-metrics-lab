with simulation_bounds as (
    select simulation_start_date as start_date, simulation_end_date_inclusive as end_date
    from {{ ref('stg_simulation_period') }}
),
calendar_days as (
    select
        generated_day::date as date_day,
        date_trunc('month', generated_day)::date as month_start
    from (
        select generate_series(start_date, end_date, interval '1 day') as generated_day
        from simulation_bounds
    ) calendar
),
month_bounds as (
    select
        month_start,
        min(date_day) as month_start_date,
        max(date_day) as month_end_date
    from calendar_days
    group by month_start
)
select
    d.date_day,
    date_trunc('month', d.date_day)::date as month_start,
    extract(year from d.date_day)::integer as calendar_year,
    extract(month from d.date_day)::integer as calendar_month,
    to_char(d.date_day, 'FMMonth') as calendar_month_name,
    (d.date_day = (b.month_start + interval '1 month - 1 day')::date) as is_month_end,
    (
        b.month_start_date = b.month_start
        and b.month_end_date + 1 = (b.month_start + interval '1 month')::date
    ) as is_complete_month
from calendar_days d
join month_bounds b using (month_start)
