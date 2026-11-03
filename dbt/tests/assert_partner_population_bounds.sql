select partner_id, month_start
from {{ ref('mart_partner_performance') }}
where is_engaged_eligible_partner and not has_available_offer
   or valid_redemption_count < 0
   or eligible_member_offer_pairs < 0
