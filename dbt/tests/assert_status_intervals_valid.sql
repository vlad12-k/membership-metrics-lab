with ordered as (
    select
        member_id,
        effective_start_date,
        effective_end_date,
        row_number() over (
            partition by member_id order by effective_start_date
        ) as interval_number,
        lag(effective_end_date) over (
            partition by member_id order by effective_start_date
        ) as previous_end_date
    from {{ ref('stg_membership_status_history') }}
)
select *
from ordered
where (effective_end_date is not null and effective_end_date <= effective_start_date)
   or (
        interval_number > 1
        and (previous_end_date is null or previous_end_date > effective_start_date)
   )
