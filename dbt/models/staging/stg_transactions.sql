
-- Staging model for transactions
-- Cleans raw_transactions: casts date, standardizes column names

SELECT
    Transaction_ID                   AS transaction_id,
    User_ID                          AS user_id,
    CAST(Transaction_Date AS DATE)   AS transaction_date,
    Amount_USD                       AS amount_usd,
    Transaction_Type                 AS transaction_type,
    Product                          AS product,
    Round_Up                         AS round_up
FROM raw_transactions
