-- Long-format cohort churn — one row per status per signup month
-- Designed for a stacked bar in Tableau:
--   Columns = cohort_month | Rows = SUM(users) | Color = status (retained & churned)

WITH users AS (
    SELECT * FROM {{ ref('mart_user_summary') }}
),

cohort AS (
    SELECT
        DATE_TRUNC('month', signup_date)              AS cohort_month,
        COUNT(*)                                      AS total_users,
        SUM(churned)                                  AS churned_users,
        COUNT(*) - SUM(churned)                       AS retained_users,
        ROUND(SUM(churned) * 100.0 / COUNT(*), 1)    AS churn_rate_pct
    FROM users
    GROUP BY DATE_TRUNC('month', signup_date)
)

SELECT
    cohort_month,
    'Churned'       AS status,
    churned_users   AS users,
    churn_rate_pct
FROM cohort

UNION ALL

SELECT
    cohort_month,
    'Retained'      AS status,
    retained_users  AS users,
    churn_rate_pct
FROM cohort

ORDER BY cohort_month, status DESC
