with reporting_months as (
    select month_start, max(date_day) as month_end_date
    from {{ ref('dim_date') }}
    group by 1
),
expected as (
    select
        p.month_start,
        (
            select count(*)::integer
            from {{ ref('stg_members') }} m
            where m.registration_date <= p.month_end_date
        ) as total_registered_members,
        (
            select count(distinct s.member_id)::integer
            from {{ ref('stg_membership_status_history') }} s
            where s.status = 'active'
              and s.effective_start_date <= p.month_end_date
              and coalesce(s.effective_end_date, 'infinity'::date) > p.month_end_date
        ) as eligible_members,
        (
            select count(distinct e.member_id)::integer
            from {{ ref('stg_member_events') }} e
            join {{ ref('stg_membership_status_history') }} event_status
              on event_status.member_id = e.member_id
             and event_status.status = 'active'
             and event_status.effective_start_date <= (e.event_at at time zone 'UTC')::date
             and coalesce(event_status.effective_end_date, 'infinity'::date)
                    > (e.event_at at time zone 'UTC')::date
            join {{ ref('stg_membership_status_history') }} snapshot_status
              on snapshot_status.member_id = e.member_id
             and snapshot_status.status = 'active'
             and snapshot_status.effective_start_date <= p.month_end_date
             and coalesce(snapshot_status.effective_end_date, 'infinity'::date) > p.month_end_date
            where e.event_type in ('offer_view', 'offer_save', 'partner_view')
              and (e.event_at at time zone 'UTC')::date between p.month_end_date - 29 and p.month_end_date
        ) as active_members_30d,
        (
            select count(distinct e.member_id)::integer
            from {{ ref('stg_member_events') }} e
            join {{ ref('stg_membership_status_history') }} s
              on s.member_id = e.member_id
             and s.status = 'active'
             and s.effective_start_date <= (e.event_at at time zone 'UTC')::date
             and coalesce(s.effective_end_date, 'infinity'::date)
                    > (e.event_at at time zone 'UTC')::date
            where e.event_type in ('offer_view', 'offer_save', 'partner_view')
              and date_trunc('month', (e.event_at at time zone 'UTC'))::date = p.month_start
        ) as monthly_active_members,
        (
            select count(distinct partner_id)::integer
            from {{ ref('stg_partners') }} s
            where s.active_from <= p.month_end_date
              and coalesce(s.active_to, 'infinity'::date) > p.month_end_date
        ) as active_partners_as_of_month_end
    from reporting_months p
)
select
    e.month_start,
    e.total_registered_members as expected_registered,
    k.total_registered_members as actual_registered,
    e.eligible_members as expected_eligible,
    k.eligible_members as actual_eligible,
    e.active_members_30d as expected_active_30d,
    k.active_members_30d as actual_active_30d,
    e.monthly_active_members as expected_mau,
    k.monthly_active_members as actual_mau,
    e.active_partners_as_of_month_end as expected_active_partners,
    k.active_partners_as_of_month_end as actual_active_partners
from expected e
join {{ ref('mart_executive_kpis') }} k using (month_start)
where e.total_registered_members is distinct from k.total_registered_members
   or e.eligible_members is distinct from k.eligible_members
   or e.active_members_30d is distinct from k.active_members_30d
   or e.monthly_active_members is distinct from k.monthly_active_members
   or e.active_partners_as_of_month_end is distinct from k.active_partners_as_of_month_end
