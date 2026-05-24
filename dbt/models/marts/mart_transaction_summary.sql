-- Monthly transaction summary by product
-- Supports balance trend over time and transaction volume by type in Tableau

WITH transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
)

SELECT
    DATE_TRUNC('month', transaction_date)   AS transaction_month,
    product,
    transaction_type,    COUNT(*)                                       AS transaction_count,
    ROUND(SUM(CASE WHEN amount_usd > 0 THEN amount_usd ELSE 0 END), 2)  AS total_deposited,
    ROUND(SUM(CASE WHEN amount_usd < 0 THEN ABS(amount_usd) ELSE 0 END), 2) AS total_withdrawn,
    ROUND(SUM(round_up), 2)                                           AS total_round_ups,
    ROUND(SUM(amount_usd), 2)                                         AS net_flow
FROM transactions
GROUP BY
    DATE_TRUNC('month', transaction_date),
    product,
    transaction_type
ORDER BY transaction_month, product, transaction_type