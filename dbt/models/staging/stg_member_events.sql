select
    event_id::varchar as event_id,
    member_id::varchar as member_id,
    event_type::varchar as event_type,
    event_at::timestamptz as event_at
from {{ ref('member_events') }}
