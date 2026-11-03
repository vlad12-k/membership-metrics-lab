with source_counts as (
    select
        date_trunc('month', redemption_date)::date as month_start,
        count(*)::integer as offer_redemption_count
    from {{ ref('fct_redemptions') }}
    group by 1
)
select
    k.month_start,
    k.offer_redemption_count as mart_count,
    coalesce(s.offer_redemption_count, 0) as source_count
from {{ ref('mart_executive_kpis') }} k
left join source_counts s using (month_start)
where k.offer_redemption_count is distinct from coalesce(s.offer_redemption_count, 0)
