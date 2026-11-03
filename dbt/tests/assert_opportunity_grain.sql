select month_start, member_id, offer_id, count(*) as row_count
from {{ ref('int_eligible_member_offer_period') }}
group by 1, 2, 3
having count(*) > 1
