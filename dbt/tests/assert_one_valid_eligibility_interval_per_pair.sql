select
    member_id,
    offer_id,
    count(*) as interval_count
from {{ ref('stg_offer_eligibility') }}
group by 1, 2
having count(*) > 1
   or bool_or(eligible_from >= eligible_to)
