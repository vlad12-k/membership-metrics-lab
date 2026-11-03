with reporting_months as (
    select
        date_trunc('month', date_day)::date as month_start,
        max(date_day) as month_end_date,
        max(date_day) + 1 as month_end_exclusive
    from {{ ref('dim_date') }}
    group by 1
)
select
    m.month_start,
    e.member_id,
    e.offer_id
from reporting_months m
join {{ ref('stg_offer_eligibility') }} e
  on e.eligible_from < m.month_end_exclusive
 and e.eligible_to > m.month_start
join {{ ref('stg_offers') }} o
  on o.offer_id = e.offer_id
 and o.valid_from < m.month_end_exclusive
 and o.valid_to > m.month_start
join {{ ref('stg_partners') }} p
  on p.partner_id = o.partner_id
 and p.active_from < m.month_end_exclusive
 and coalesce(p.active_to, 'infinity'::date) > m.month_start
where greatest(e.eligible_from, o.valid_from, p.active_from, m.month_start)
    < least(e.eligible_to, o.valid_to, coalesce(p.active_to, 'infinity'::date), m.month_end_exclusive)
  and exists (
      select 1 from {{ ref('stg_membership_status_history') }} s
      where s.member_id = e.member_id
        and s.status = 'active'
        and s.effective_start_date < m.month_end_exclusive
        and coalesce(s.effective_end_date, 'infinity'::date) > m.month_start
        and greatest(e.eligible_from, o.valid_from, p.active_from, s.effective_start_date, m.month_start)
            < least(e.eligible_to, o.valid_to, coalesce(p.active_to, 'infinity'::date),
                    coalesce(s.effective_end_date, 'infinity'::date), m.month_end_exclusive)
  )
