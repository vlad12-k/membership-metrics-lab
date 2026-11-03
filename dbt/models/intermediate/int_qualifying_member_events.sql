select
    e.event_id,
    e.member_id,
    e.event_type,
    e.event_at,
    (e.event_at at time zone 'UTC')::date as event_date
from {{ ref('stg_member_events') }} e
where e.event_type in ('offer_view', 'offer_save', 'partner_view')
  and exists (
      select 1 from {{ ref('stg_membership_status_history') }} s
      where s.member_id = e.member_id
        and s.status = 'active'
        and s.effective_start_date <= (e.event_at at time zone 'UTC')::date
        and coalesce(s.effective_end_date, 'infinity'::date) > (e.event_at at time zone 'UTC')::date
  )
