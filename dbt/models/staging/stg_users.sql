-- Staging model for users
-- Cleans raw_users: casts date, renames nothing (columns already clean)

SELECT
    User_ID                          AS user_id,
    CAST(Signup_Date     AS DATE)    AS signup_date,
    Acquisition_Channel              AS acquisition_channel,
    Account_Type                     AS account_type,
    State                            AS state,
    Age_Group                        AS age_group
FROM raw_users
