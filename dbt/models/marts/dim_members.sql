select
    member_id,
    registration_date,
    date_trunc('month', registration_date)::date as cohort_month
from {{ ref('stg_members') }}
