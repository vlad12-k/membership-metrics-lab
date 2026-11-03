with cohort_sizes as (
    select cohort_month, count(*)::integer as cohort_size
    from {{ ref('dim_members') }}
    group by 1
),
member_months as (
    select
        cohort_month,
        (
            (extract(year from month_start) - extract(year from cohort_month)) * 12
            + extract(month from month_start) - extract(month from cohort_month)
        )::integer as age_month,
        is_monthly_active,
        is_complete_month
    from {{ ref('mart_member_engagement') }}
),
cohort_activity as (
    select
        cohort_month,
        age_month,
        count(*) filter (where is_monthly_active and is_complete_month)::integer as retained_members,
        bool_and(is_complete_month) as is_complete_month
    from member_months
    group by 1, 2
)
select
    a.cohort_month,
    a.age_month,
    s.cohort_size,
    a.retained_members,
    a.is_complete_month,
    case
        when a.is_complete_month then a.retained_members::numeric / nullif(s.cohort_size, 0)
        else null
    end as cohort_retention_rate
from cohort_activity a
join cohort_sizes s using (cohort_month)
