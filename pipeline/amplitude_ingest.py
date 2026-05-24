import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────

# Set your Amplitude Project API Key as an environment variable:
#   PowerShell:  $env:AMPLITUDE_API_KEY = "your_key_here"
#   Mac/Linux:   export AMPLITUDE_API_KEY="your_key_here"
AMPLITUDE_API_KEY = os.environ.get("AMPLITUDE_API_KEY", "")

BATCH_ENDPOINT    = "https://api2.amplitude.com/batch"     # up to 2000 events per call
IDENTIFY_ENDPOINT = "https://api.amplitude.com/identify"   # user property updates

EVENT_BATCH_SIZE    = 500   # events per HTTP request
IDENTIFY_BATCH_SIZE = 100   # identify calls per HTTP request
REQUEST_DELAY_SEC   = 0.2   # pause between requests to stay within rate limits

PROJECT_DIR = Path(__file__).resolve().parent.parent
USER_PROFILE_PATH = PROJECT_DIR / "exports" / "mart_user_summary.csv"
EVENTS_PATH = PROJECT_DIR / "data" / "events.csv"

# ─────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load user profiles and events for Amplitude ingestion."""
    if not USER_PROFILE_PATH.exists():
        raise FileNotFoundError(f"Missing user profile file: {USER_PROFILE_PATH}")
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(f"Missing events file: {EVENTS_PATH}")

    users = pd.read_csv(USER_PROFILE_PATH)
    events = pd.read_csv(EVENTS_PATH)
    return users, events


# ─────────────────────────────────────────
# User Properties  (Amplitude Identify API)
# ─────────────────────────────────────────

def build_identifications(users: pd.DataFrame) -> list[dict]:
    """
    Map each user row to an Amplitude identify object.

    Sets persistent user properties so every downstream chart in Amplitude
    can be segmented by:
        account_type, acquisition_channel, age_group, state, churned
    """
    identifications = []
    for _, row in users.iterrows():
        identifications.append({
            "user_id": f"user_{row['User_ID']}",
            "user_properties": {
                "$set": {
                    "signup_date":          row["Signup_Date"],
                    "acquisition_channel":  row["Acquisition_Channel"],
                    "account_type":         row["Account_Type"],
                    "state":                row["State"],
                    "age_group":            row["Age_Group"],
                    "churned":              bool(row["Churned"]),
                    "churn_type":           str(row["Churn_Type"]) if pd.notna(row["Churn_Type"]) else "Active",
                }
            },
        })
    return identifications


def send_user_properties(users: pd.DataFrame) -> None:
    """Send user identify calls in batches to Amplitude."""
    identifications = build_identifications(users)
    total = len(identifications)

    for i in range(0, total, IDENTIFY_BATCH_SIZE):
        batch = identifications[i : i + IDENTIFY_BATCH_SIZE]
        payload = {
            "api_key":        AMPLITUDE_API_KEY,
            "identification": json.dumps(batch),
        }
        response = requests.post(IDENTIFY_ENDPOINT, data=payload, timeout=10)
        response.raise_for_status()
        print(f"  Users identified: {min(i + IDENTIFY_BATCH_SIZE, total)}/{total}")
        time.sleep(REQUEST_DELAY_SEC)


# ─────────────────────────────────────────
# Events  (Amplitude Batch API)
# ─────────────────────────────────────────

def build_amplitude_events(events: pd.DataFrame) -> list[dict]:
    """
    Map each event row to an Amplitude event object.

    Event Types tracked:
        Login | View_Portfolio | Deposit | Withdrawal | View_Statement

    These five events cover the core Investing and Banking journeys and
    directly support the following Amplitude analyses:
        - Investing funnel:   Login → View_Portfolio → Deposit
        - Banking funnel:     Login → Deposit | Withdrawal
        - Retention:          cohort-based user retention by signup month
        - Segmentation:       events by Platform, Account_Type, Acquisition_Channel
        - Session analysis:   avg session_duration_sec by Event_Type and churn status
    """
    amplitude_events = []
    for _, row in events.iterrows():
        # Amplitude requires time in epoch milliseconds
        event_time_ms = int(pd.Timestamp(row["Event_Date"]).timestamp() * 1000)

        amplitude_events.append({
            "user_id":    f"user_{row['User_ID']}",
            "event_type": row["Event_Type"],
            "time":       event_time_ms,
            "platform":   row["Platform"],
            "event_properties": {
                "platform":             row["Platform"],
                "session_duration_sec": int(row["Session_Duration_Sec"]),
            },
        })
    return amplitude_events


def send_events(amplitude_events: list[dict]) -> None:
    """Send events to Amplitude in batches using the Batch API."""
    total = len(amplitude_events)

    for i in range(0, total, EVENT_BATCH_SIZE):
        batch = amplitude_events[i : i + EVENT_BATCH_SIZE]
        payload = {
            "api_key": AMPLITUDE_API_KEY,
            "events":  batch,
        }
        response = requests.post(
            BATCH_ENDPOINT,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=15,
        )
        if not response.ok:
            print(f"  Amplitude error {response.status_code}: {response.text}")
        response.raise_for_status()
        print(f"  Events sent: {min(i + EVENT_BATCH_SIZE, total)}/{total}")
        time.sleep(REQUEST_DELAY_SEC)


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main() -> None:
    if not AMPLITUDE_API_KEY:
        print(
            "ERROR: Amplitude API key not set.\n"
            "  PowerShell:  $env:AMPLITUDE_API_KEY = 'your_key_here'\n"
            "  Mac/Linux:   export AMPLITUDE_API_KEY='your_key_here'\n"
            "Then re-run this script."
        )
        return

    try:
        print("Loading data...")
        users, events = load_data()
        print(f"  {len(users)} users, {len(events)} events loaded\n")

        print("Step 1/2 — Sending user properties to Amplitude (Identify API)...")
        send_user_properties(users)

        print("\nStep 2/2 — Sending events to Amplitude (Batch API)...")
        amplitude_events = build_amplitude_events(events)
        send_events(amplitude_events)

        print(
            f"\nDone. {len(users)} user profiles and {len(amplitude_events)} events "
            "successfully sent to Amplitude."
        )
        print(
            "\nNext steps in Amplitude:\n"
            "  1. Event Segmentation  — chart Login, View_Portfolio, Deposit by Platform & Account_Type\n"
            "  2. Funnel Analysis     — Login → View_Portfolio → Deposit (Investing conversion funnel)\n"
            "  3. Retention Analysis  — cohort retention grid by Signup_Date\n"
            "  4. User Lookup         — verify user properties (account_type, churned, age_group)\n"
            "  5. Pathfinder          — explore event sequences leading to Withdrawal or churn"
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
    except requests.RequestException as exc:
        print(f"ERROR: Amplitude request failed: {exc}")
    except Exception as exc:
        print(f"ERROR: Unexpected failure: {exc}")


if __name__ == "__main__":
    main()
