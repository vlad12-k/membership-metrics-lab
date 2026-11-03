select partner_id, month_start, count(*) as row_count
from {{ ref('mart_partner_performance') }}
group by 1, 2
having count(*) > 1
