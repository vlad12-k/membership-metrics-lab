select
    partner_id::varchar as partner_id,
    category_id::varchar as category_id,
    active_from::date as active_from,
    active_to::date as active_to
from {{ ref('partners') }}
