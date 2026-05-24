-- Staging model for events
-- Cleans raw_events: casts date, standardizes column names

SELECT
    Event_ID,
    User_ID,
    CAST(Event_Date AS DATE)         AS event_date,
    Event_Type                       AS event_type,
    Platform                         AS platform,
    Session_Duration_Sec             AS session_duration_sec
FROM raw_events