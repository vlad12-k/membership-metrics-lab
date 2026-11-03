select member_id, month_start, count(*) as row_count
from {{ ref('mart_member_engagement') }}
group by 1, 2
having count(*) > 1
