with redemptions as (
    select * from {{ ref('stg_redemptions') }}
),
classified as (
    select
        r.redemption_id,
        r.member_id,
        r.offer_id,
        r.redeemed_at,
        (r.redeemed_at at time zone 'UTC')::date as redemption_date,
        r.status,
        (r.status = 'complete') as is_complete_status,
        (o.offer_id is not null) as offer_exists,
        (
            o.offer_id is not null
            and o.valid_from <= (r.redeemed_at at time zone 'UTC')::date
            and (r.redeemed_at at time zone 'UTC')::date < o.valid_to
        ) as within_offer_period,
        (e.member_id is not null) as member_offer_eligible,
        (s.member_id is not null) as member_active_on_redemption
    from redemptions r
    left join {{ ref('stg_offers') }} o
      on o.offer_id = r.offer_id
    left join {{ ref('stg_offer_eligibility') }} e
      on e.member_id = r.member_id
     and e.offer_id = r.offer_id
     and e.eligible_from <= (r.redeemed_at at time zone 'UTC')::date
     and (r.redeemed_at at time zone 'UTC')::date < e.eligible_to
    left join {{ ref('stg_membership_status_history') }} s
      on s.member_id = r.member_id
     and s.status = 'active'
     and s.effective_start_date <= (r.redeemed_at at time zone 'UTC')::date
     and coalesce(s.effective_end_date, 'infinity'::date) > (r.redeemed_at at time zone 'UTC')::date
)
select
    *,
    is_complete_status and offer_exists and within_offer_period
        and member_offer_eligible and member_active_on_redemption as is_valid_redemption,
    case
        when not is_complete_status then 'non_complete_status'
        when not offer_exists then 'missing_offer'
        when not within_offer_period then 'outside_offer_validity'
        when not member_active_on_redemption then 'inactive_membership'
        when not member_offer_eligible then 'not_offer_eligible'
        else null
    end as rejection_reason
from classified
