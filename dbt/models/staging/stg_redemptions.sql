select
    redemption_id::varchar as redemption_id,
    member_id::varchar as member_id,
    offer_id::varchar as offer_id,
    redeemed_at::timestamptz as redeemed_at,
    status::varchar as status
from {{ ref('redemptions') }}
