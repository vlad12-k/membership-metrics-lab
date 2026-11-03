select
    r.redemption_id,
    r.member_id,
    r.offer_id,
    o.partner_id,
    p.category_id,
    r.redeemed_at,
    r.redemption_date,
    r.status
from {{ ref('int_redemption_validation') }} r
join {{ ref('dim_offers') }} o using (offer_id)
join {{ ref('dim_partners') }} p using (partner_id)
where r.is_valid_redemption
