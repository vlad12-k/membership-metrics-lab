with reporting_months as (
    select
        month_start,
        max(date_day) as month_end_date,
        bool_and(is_complete_month) as is_complete_month
    from {{ ref('dim_date') }}
    group by 1
),
member_metrics as (
    select
        month_start,
        count(*)::integer as total_registered_members,
        count(*) filter (where is_eligible_as_of_month_end)::integer as eligible_members,
        count(*) filter (where is_active_30d_as_of_month_end)::integer as active_members_30d,
        count(*) filter (where is_monthly_active)::integer as monthly_active_members
    from {{ ref('mart_member_engagement') }}
    group by 1
),
eligible_pairs as (
    select month_start, count(*)::integer as eligible_member_offer_pairs
    from {{ ref('int_eligible_member_offer_period') }}
    group by 1
),
redeemed_pairs as (
    select
        date_trunc('month', redemption_date)::date as month_start,
        count(distinct (member_id, offer_id))::integer as redeemed_member_offer_pairs
    from {{ ref('fct_redemptions') }}
    group by 1
),
redemption_member_counts as (
    select date_trunc('month', redemption_date)::date as month_start, member_id, count(*) as redemption_count
    from {{ ref('fct_redemptions') }}
    group by 1, 2
),
redemption_metrics as (
    select
        month_start,
        sum(redemption_count)::integer as offer_redemption_count,
        count(*)::integer as members_with_redemption,
        count(*) filter (where redemption_count >= 2)::integer as repeat_redeemers
    from redemption_member_counts
    group by 1
),
partner_metrics as (
    select
        month_start,
        count(*) filter (where is_active_as_of_month_end)::integer as active_partners_as_of_month_end,
        count(*) filter (where has_available_offer)::integer as partner_offer_available_count,
        count(*) filter (where is_engaged_eligible_partner)::integer as engaged_eligible_partner_count
    from {{ ref('mart_partner_performance') }}
    group by 1
)
select
    p.month_start,
    p.month_end_date,
    p.is_complete_month,
    coalesce(m.total_registered_members, 0) as total_registered_members,
    coalesce(m.eligible_members, 0) as eligible_members,
    coalesce(m.active_members_30d, 0) as active_members_30d,
    coalesce(m.monthly_active_members, 0) as monthly_active_members,
    coalesce(r.offer_redemption_count, 0) as offer_redemption_count,
    coalesce(e.eligible_member_offer_pairs, 0) as eligible_member_offer_pairs,
    coalesce(rp.redeemed_member_offer_pairs, 0) as redeemed_member_offer_pairs,
    rp.redeemed_member_offer_pairs::numeric / nullif(e.eligible_member_offer_pairs, 0)
        as offer_redemption_rate,
    coalesce(pm.active_partners_as_of_month_end, 0) as active_partners_as_of_month_end,
    coalesce(pm.partner_offer_available_count, 0) as partner_offer_available_count,
    coalesce(pm.engaged_eligible_partner_count, 0) as engaged_eligible_partner_count,
    pm.engaged_eligible_partner_count::numeric / nullif(pm.partner_offer_available_count, 0)
        as partner_engagement_rate,
    coalesce(r.members_with_redemption, 0) as members_with_redemption,
    coalesce(r.repeat_redeemers, 0) as repeat_redeemers,
    r.repeat_redeemers::numeric / nullif(r.members_with_redemption, 0) as repeat_redemption_rate
from reporting_months p
left join member_metrics m using (month_start)
left join eligible_pairs e using (month_start)
left join redeemed_pairs rp using (month_start)
left join redemption_metrics r using (month_start)
left join partner_metrics pm using (month_start)
