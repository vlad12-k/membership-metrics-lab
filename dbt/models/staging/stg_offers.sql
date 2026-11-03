select
    offer_id::varchar as offer_id,
    partner_id::varchar as partner_id,
    offer_title::varchar as offer_title,
    valid_from::date as valid_from,
    valid_to::date as valid_to
from {{ ref('offers') }}
