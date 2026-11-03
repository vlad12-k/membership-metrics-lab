with period as (
    select simulation_start_date, simulation_end_date_inclusive
    from {{ ref('stg_simulation_period') }}
)
select
    count(*) as observed_dates,
    min(date_day) as first_date,
    max(date_day) as last_date
from {{ ref('dim_date') }}
having min(date_day) <> (select simulation_start_date from period)
    or max(date_day) <> (select simulation_end_date_inclusive from period)
    or count(*) <> max(date_day) - min(date_day) + 1
