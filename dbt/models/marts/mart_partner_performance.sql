with reporting_months as (
    select
        month_start,
        max(date_day) as month_end_date,
        max(date_day) + 1 as month_end_exclusive
    from {{ ref('dim_date') }}
    group by 1
),
partner_months as (
    select p.partner_id, p.category_id, p.category_name, m.month_start, m.month_end_date, m.month_end_exclusive
    from {{ ref('dim_partners') }} p
    join reporting_months m
      on p.active_from < m.month_end_exclusive
     and coalesce(p.active_to, 'infinity'::date) > m.month_start
),
availability as (
    select
        o.partner_id,
        e.month_start,
        count(*) as eligible_member_offer_pairs
    from {{ ref('int_eligible_member_offer_period') }} e
    join {{ ref('dim_offers') }} o using (offer_id)
    group by 1, 2
),
redemptions as (
    select
        partner_id,
        date_trunc('month', redemption_date)::date as month_start,
        count(*) as valid_redemption_count
    from {{ ref('fct_redemptions') }}
    group by 1, 2
)
select
    p.partner_id,
    p.category_id,
    p.category_name,
    p.month_start,
    p.month_end_date,
    exists (
        select 1 from {{ ref('dim_partners') }} d
        where d.partner_id = p.partner_id
          and d.active_from <= p.month_end_date
          and coalesce(d.active_to, 'infinity'::date) > p.month_end_date
    ) as is_active_as_of_month_end,
    coalesce(a.eligible_member_offer_pairs, 0)::integer as eligible_member_offer_pairs,
    coalesce(a.eligible_member_offer_pairs, 0) > 0 as has_available_offer,
    coalesce(r.valid_redemption_count, 0)::integer as valid_redemption_count,
    coalesce(a.eligible_member_offer_pairs, 0) > 0
      and coalesce(r.valid_redemption_count, 0) > 0 as is_engaged_eligible_partner
from partner_months p
left join availability a using (partner_id, month_start)
left join redemptions r using (partner_id, month_start)
