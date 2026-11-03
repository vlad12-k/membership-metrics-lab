select cohort_month, age_month
from {{ ref('mart_cohort_retention') }}
where retained_members > cohort_size
   or (is_complete_month and cohort_size = 0 and cohort_retention_rate is not null)
   or (not is_complete_month and cohort_retention_rate is not null)
   or (cohort_size > 0 and is_complete_month and cohort_retention_rate is null)
