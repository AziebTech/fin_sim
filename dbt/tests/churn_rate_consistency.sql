-- Ensures cohort churn rates are consistent with the underlying cohort counts.
SELECT
  cohort_month,
  total_users,
  churned_users,
  churn_rate_pct,
  ROUND(churned_users * 100.0 / NULLIF(total_users, 0), 1) AS expected_churn_rate_pct
FROM {{ ref('mart_churn_cohort') }}
WHERE total_users = 0
   OR churn_rate_pct != ROUND(churned_users * 100.0 / NULLIF(total_users, 0), 1)
