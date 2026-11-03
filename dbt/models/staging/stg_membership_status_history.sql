select
    member_id::varchar as member_id,
    status::varchar as status,
    effective_start_date::date as effective_start_date,
    effective_end_date::date as effective_end_date
from {{ ref('membership_status_history') }}
