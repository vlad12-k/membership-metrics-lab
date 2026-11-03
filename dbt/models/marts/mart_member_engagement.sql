with reporting_months as (
    select
        month_start,
        max(date_day) as month_end_date,
        bool_and(is_complete_month) as is_complete_month
    from {{ ref('dim_date') }}
    group by 1
),
member_months as (
    select
        m.member_id,
        m.registration_date,
        m.cohort_month,
        p.month_start,
        p.month_end_date,
        p.is_complete_month
    from {{ ref('dim_members') }} m
    join reporting_months p on m.registration_date <= p.month_end_date
),
active_status as (
    select m.member_id, m.month_start
    from member_months m
    join {{ ref('stg_membership_status_history') }} s
      on s.member_id = m.member_id
     and s.status = 'active'
     and s.effective_start_date <= m.month_end_date
     and coalesce(s.effective_end_date, 'infinity'::date) > m.month_end_date
    group by 1, 2
),
activity as (
    select
        e.member_id,
        p.month_start,
        count(*) filter (
            where e.event_date between p.month_start and p.month_end_date
        ) as qualifying_event_count,
        count(*) filter (
            where e.event_date between p.month_end_date - 29 and p.month_end_date
        ) as qualifying_event_count_30d
    from {{ ref('int_qualifying_member_events') }} e
    join reporting_months p
      on e.event_date between least(p.month_start, p.month_end_date - 29) and p.month_end_date
    group by 1, 2
)
select
    m.member_id,
    m.registration_date,
    m.cohort_month,
    m.month_start,
    m.month_end_date,
    m.is_complete_month,
    (s.member_id is not null) as is_eligible_as_of_month_end,
    coalesce(a.qualifying_event_count, 0) > 0 as is_monthly_active,
    coalesce(a.qualifying_event_count_30d, 0) > 0 and (s.member_id is not null)
        as is_active_30d_as_of_month_end,
    coalesce(a.qualifying_event_count, 0)::integer as qualifying_event_count,
    coalesce(a.qualifying_event_count_30d, 0)::integer as qualifying_event_count_30d
from member_months m
left join active_status s using (member_id, month_start)
left join activity a using (member_id, month_start)
