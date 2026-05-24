-- One row per user — combines users + transactions + events into a single analytics table
-- Powers: churn by segment, churn type (explicit vs silent), balance trend, user activity views in Tableau

WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
),

events AS (
    SELECT * FROM {{ ref('stg_events') }}
),

-- Flag users who fired an explicit Cancel_Account event
-- Used to split churned users into Explicit vs Silent segments
cancelled AS (
    SELECT DISTINCT user_id
    FROM events
    WHERE event_type = 'Cancel_Account'
),

-- Aggregate all transaction metrics per user
tx_summary AS (
    SELECT
        user_id,
        COUNT(*)                                                AS total_transactions,
        SUM(CASE WHEN amount_usd > 0 THEN amount_usd ELSE 0 END)  AS total_deposited,
        SUM(CASE WHEN amount_usd < 0 THEN ABS(amount_usd) ELSE 0 END) AS total_withdrawn,
        SUM(round_up)                                           AS total_round_ups,
        SUM(amount_usd)                                         AS running_balance,
        MIN(transaction_date)                                   AS first_transaction_date,
        MAX(transaction_date)                                   AS last_transaction_date
    FROM transactions
    GROUP BY user_id
),

-- Aggregate all event metrics per user
ev_summary AS (
    SELECT
        user_id,
        COUNT(*)            AS total_events,
        MAX(event_date)     AS last_event_date,
        AVG(session_duration_sec) AS avg_session_duration_sec
    FROM events
    GROUP BY user_id
)

SELECT
    u.user_id,
    u.signup_date,
    u.acquisition_channel,
    u.account_type,
    u.state,
    u.age_group,

    -- Churn logic: churned if no transactions, OR if last transaction was > 90 days ago relative to sim end
    CASE
        WHEN t.last_transaction_date IS NULL THEN 1
        WHEN DATE_DIFF('day', t.last_transaction_date, DATE '2026-05-05') > 90 THEN 1
        ELSE 0
    END AS churned,

    -- Churn type derived from events — 'Explicit' = fired Cancel_Account event | 'Silent' = transactional inactivity | 'None' = retained
    CASE
        WHEN c.user_id IS NOT NULL THEN 'Explicit'
        WHEN t.last_transaction_date IS NULL OR DATE_DIFF('day', t.last_transaction_date, DATE '2026-05-05') > 90 THEN 'Silent'
        ELSE 'Active'
    END AS churn_type,

    -- Transaction metrics (default to 0 if user has no transactions)
    COALESCE(t.total_transactions,    0)     AS total_transactions,
    COALESCE(t.total_deposited,       0)     AS total_deposited,
    COALESCE(t.total_withdrawn,       0)     AS total_withdrawn,
    COALESCE(t.total_round_ups,       0)     AS total_round_ups,
    COALESCE(t.running_balance,       0)     AS running_balance,
    t.first_transaction_date,
    t.last_transaction_date,

    -- Days since last transaction as of end of observation period (2026-05-05)
    -- Rolling inactivity signal: > 90 days = churned threshold
    CASE
        WHEN t.last_transaction_date IS NULL THEN NULL
        ELSE DATE_DIFF('day', t.last_transaction_date, DATE '2026-05-05')
    END AS days_since_last_transaction,

    -- Event metrics
    COALESCE(e.total_events,          0)     AS total_events,
    e.last_event_date,
    COALESCE(e.avg_session_duration_sec, 0)  AS avg_session_duration_sec

FROM users u
LEFT JOIN tx_summary t  ON u.user_id = t.user_id
LEFT JOIN ev_summary e  ON u.user_id = e.user_id
LEFT JOIN cancelled  c  ON u.user_id = c.user_id