select
    member_id::varchar as member_id,
    offer_id::varchar as offer_id,
    eligible_from::date as eligible_from,
    eligible_to::date as eligible_to
from {{ ref('offer_eligibility') }}
