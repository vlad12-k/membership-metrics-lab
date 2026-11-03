select
    member_id::varchar as member_id,
    registration_date::date as registration_date
from {{ ref('members') }}
