select
    offer_id,
    partner_id,
    offer_title,
    valid_from,
    valid_to
from {{ ref('stg_offers') }}
