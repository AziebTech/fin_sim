-- Validates that churn type labels are consistent with explicit churn events and inactivity thresholds.
SELECT
  u.user_id,
  u.churn_type,
  u.churned,
  u.days_since_last_transaction,
  -- Flag the type of logic issue found for each user
  CASE
    WHEN u.churn_type = 'Explicit' THEN 'explicit_missing_event'      -- Marked as Explicit churn but no Cancel_Account event found
    WHEN u.churn_type = 'Silent' THEN 'silent_too_recent'             -- Marked as Silent churn but last transaction was too recent
    WHEN u.churn_type = 'Active' THEN 'active_marked_churned'         -- Marked as Active but churned flag is set
  END AS issue
FROM {{ ref('mart_user_summary') }} u
LEFT JOIN (
  SELECT DISTINCT user_id
  FROM {{ ref('stg_events') }}
  WHERE event_type = 'Cancel_Account'   -- Find users with explicit cancel events
) c ON u.user_id = c.user_id
WHERE
  -- 1. Explicit churners missing a Cancel_Account event
  (u.churn_type = 'Explicit' AND c.user_id IS NULL)
  -- 2. Silent churners whose last transaction was within 90 days (should not be churned)
  OR (u.churn_type = 'Silent' AND COALESCE(u.days_since_last_transaction, 0) <= 90)
  -- 3. Active users who are incorrectly marked as churned
  OR (u.churn_type = 'Active' AND u.churned = 1)
