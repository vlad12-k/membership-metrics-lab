with source_counts as (
    select date_trunc('month', event_date)::date as month_start, count(distinct member_id) as monthly_active_members
    from {{ ref('int_qualifying_member_events') }}
    group by 1
)
select
    k.month_start,
    k.monthly_active_members as mart_count,
    coalesce(s.monthly_active_members, 0)::integer as source_count
from {{ ref('mart_executive_kpis') }} k
left join source_counts s using (month_start)
where k.monthly_active_members is distinct from coalesce(s.monthly_active_members, 0)::integer
