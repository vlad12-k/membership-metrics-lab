select
    period_id::varchar as period_id,
    simulation_start_date::date as simulation_start_date,
    simulation_end_date_inclusive::date as simulation_end_date_inclusive,
    seed::integer as seed,
    schema_version::varchar as schema_version
from {{ ref('simulation_period') }}
