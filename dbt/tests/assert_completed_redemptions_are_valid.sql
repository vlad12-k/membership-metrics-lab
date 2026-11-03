select redemption_id, rejection_reason
from {{ ref('int_redemption_validation') }}
where status = 'complete'
  and not is_valid_redemption
