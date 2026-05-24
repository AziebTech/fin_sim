-- Cohort churn analysis — one row per signup month
-- Supports cohort retention heatmap in Tableau

WITH users AS (
    SELECT * FROM {{ ref('mart_user_summary') }}
)

SELECT
    -- Truncate signup date to the first of the month (e.g. 2025-06-14 → 2025-06-01)
    DATE_TRUNC('month', signup_date)    AS cohort_month,
    COUNT(*)                            AS total_users,
    SUM(churned)                        AS churned_users,
    COUNT(*) - SUM(churned)             AS retained_users,
    ROUND(SUM(churned) * 100.0 / COUNT(*), 1) AS churn_rate_pct,
    SUM(CASE WHEN churn_type = 'Explicit' THEN 1 ELSE 0 END) AS explicit_churners,
    SUM(CASE WHEN churn_type = 'Silent'   THEN 1 ELSE 0 END) AS silent_churners,
    ROUND(SUM(CASE WHEN churn_type = 'Explicit' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS explicit_churn_rate_pct,
    ROUND(SUM(CASE WHEN churn_type = 'Silent'   THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS silent_churn_rate_pct
    
FROM users
GROUP BY DATE_TRUNC('month', signup_date)
ORDER BY cohort_month