select
    p.partner_id,
    p.category_id,
    c.category_name,
    p.active_from,
    p.active_to
from {{ ref('stg_partners') }} p
join {{ ref('stg_partner_categories') }} c using (category_id)
