select month_start
from {{ ref('mart_executive_kpis') }}
where eligible_members > total_registered_members
   or active_members_30d > eligible_members
   or redeemed_member_offer_pairs > eligible_member_offer_pairs
   or engaged_eligible_partner_count > partner_offer_available_count
   or repeat_redeemers > members_with_redemption
   or offer_redemption_count < 0
