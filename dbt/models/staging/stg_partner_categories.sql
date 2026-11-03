select
    category_id::varchar as category_id,
    category_name::varchar as category_name
from {{ ref('partner_categories') }}
