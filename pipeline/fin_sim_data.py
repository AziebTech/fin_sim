import pandas as pd
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
# Generate synthetic banking and investment data.
# Export three CSV tables: users, transactions, and events.

np.random.seed(38)

NUM_USERS        = 500
NUM_TRANSACTIONS = 8000
NUM_EVENTS       = 12000
SIM_START        = pd.Timestamp("2025-05-05")  # Start day of simulation period.
SIM_END          = pd.Timestamp("2026-05-05")    # End day of simulation period.
CHURN_CUTOFF     = SIM_END - pd.Timedelta(days=90)  # Establish a 90-day rolling inactivity window.

# Create the output data directory at the project root.
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data"

# If the folder already exists, no error is raised and execution continues.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# Table 1 — users
# Generate the users table for analytics and modeling.
# ─────────────────────────────────────────

# Create sequential user IDs from 1001 to 1500
user_ids = np.arange(1001, 1001 + NUM_USERS)

# Generate vectorized signup dates between SIM_START and SIM_END
# Offsets are created in bulk and converted to timedeltas for performance.
signup_offsets = np.random.randint(0, (SIM_END - SIM_START).days, size=NUM_USERS)
signup_dates   = SIM_START + pd.to_timedelta(signup_offsets, unit="D")

# Marketing traffic sources
channels      = ["Organic", "Referral", "Paid Social", "Email", "App Store"] 

# Probability that each marketing channel converts a business visitor into a customer, in the same order as the `channels` list
channel_probs = [0.35, 0.20, 0.25, 0.10, 0.10] 

# Available financial products
account_types      = ["Banking", "Invest", "Both"] 

# Probability that each account type is used by a customer, in the same order as the `account_types` list
account_type_probs = [0.40, 0.35, 0.25] 

# List of U.S. state abbreviations used for customer locations
states = ["CA", "TX", "NY", "FL", "IL", "WA", "CO", "GA", "OH", "AZ"]

# List of age group categories used for demographic segmentation
age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]

# Probabilities aligned to the `age_groups` order
age_group_probs = [0.20, 0.35, 0.25, 0.12, 0.08]

# Ensure probability lists sum to 1.0 to prevent NumPy sampling errors
assert abs(sum(channel_probs)      - 1.0) < 1e-6, "channel_probs must sum to 1"
assert abs(sum(account_type_probs) - 1.0) < 1e-6, "account_type_probs must sum to 1"
assert abs(sum(age_group_probs)    - 1.0) < 1e-6, "age_group_probs must sum to 1"

# Build the users DataFrame
users_df = pd.DataFrame({
    # Customer identifier
    "User_ID":          user_ids,
    # User signup date within the simulation window
    "Signup_Date":      signup_dates,
    # Acquisition channel assigned based on the channel probability distribution
    "Acquisition_Channel": np.random.choice(channels, size=NUM_USERS, p=channel_probs),
    # Product account type assigned based on the account type distribution
    "Account_Type":     np.random.choice(account_types, size=NUM_USERS, p=account_type_probs),
    # User home state assigned from the state list
    "State":            np.random.choice(states, size=NUM_USERS),
    # Age group assigned based on the age group probability distribution
    "Age_Group":        np.random.choice(age_groups, size=NUM_USERS, p=age_group_probs),
})

# Example output - ASCII format
# +---------+-------------+----------------------+--------------+-------+-----------+
# | User_ID | Signup_Date | Acquisition_Channel  | Account_Type | State | Age_Group |
# +---------+-------------+----------------------+--------------+-------+-----------+
# |    1001 |  2025-06-14 | Organic              | Banking      | CA    | 25-34     |
# |    1002 |  2025-09-02 | Paid Social          | Invest       | TX    | 35-44     |
# |    1003 |  2025-04-21 | Referral             | Both         | NY    | 25-34     |
# |    1004 |  2025-11-30 | Email                | Banking      | FL    | 18-24     |
# |    1005 |  2025-07-08 | Organic              | Invest       | WA    | 25-34     |
# +---------+-------------+----------------------+--------------+-------+-----------+

print("── Users ──────────────────────────────")

# Print the first five users without showing the DataFrame index
print(users_df.head(5).to_string(index=False))


# ─────────────────────────────────────────
# Table 2 — transactions
# Generate the transactions table for analytics.
# ─────────────────────────────────────────

# Assign a user ID to each transaction
tx_user_ids = np.random.choice(user_ids, size=NUM_TRANSACTIONS)

# Build a lookup for signup dates by user ID
signup_lookup = users_df.set_index("User_ID")["Signup_Date"].to_dict()

# ─────────────────────────────────────────
# Disengagement model - Weibull survival distribution
# Each user draws an activity lifespan after signup.
# A Weibull(shape=1.5, scale=600) lifetime creates a realistic customer lifecycle:
#   - shape > 1 implies an increasing hazard over time.
#   - scale=600 centers the lifespan so a minority of users disengage within the sim window.
# This phase produces user activity horizons; churn is inferred later by comparing activity_end_date against CHURN_CUTOFF.
# ─────────────────────────────────────────
np.random.seed(42)
_lifespans         = np.random.weibull(1.5, size=NUM_USERS) * 600  # days active after signup
_lifespan_lookup   = dict(zip(user_ids, _lifespans))

# activity_end_date = signup + lifespan, then clipped to SIM_END (users cannot remain active beyond the simulation window)
_signup_series     = users_df.set_index("User_ID")["Signup_Date"]
_lifespan_series   = pd.Series(_lifespan_lookup)
_activity_end_raw  = _signup_series + pd.to_timedelta(_lifespan_series.round().astype(int), unit="D")
_activity_end_clip = _activity_end_raw.clip(upper=SIM_END)
activity_end_lookup = _activity_end_clip.to_dict()

# Vectorized date generation using .map() — faster than explicit Python loops.
tx_start_dates = pd.Series(tx_user_ids).map(signup_lookup)
# Cap each transaction date to the user's Weibull-derived activity_end_date.
tx_end_dates   = pd.Series(tx_user_ids).map(activity_end_lookup)
tx_days_avail  = ((tx_end_dates - tx_start_dates).dt.days).clip(lower=1)
tx_offsets     = (np.random.uniform(0, 1, NUM_TRANSACTIONS) * tx_days_avail).astype(int)
tx_dates       = tx_start_dates + pd.to_timedelta(tx_offsets, unit="D")

tx_types      = ["Round-Up", "One-Time Deposit", "Recurring Deposit", "Withdrawal"]
tx_type_probs = [0.45, 0.20, 0.25, 0.10]

tx_products      = ["Banking", "Invest"]
tx_product_probs = [0.55, 0.45]

assert abs(sum(tx_type_probs)    - 1.0) < 1e-6, "tx_type_probs must sum to 1"
assert abs(sum(tx_product_probs) - 1.0) < 1e-6, "tx_product_probs must sum to 1"

# Link product to each user's account type so banking-only users never get invest transactions and downstream joins/filters remain accurate.
# Banking → always "Banking" | Invest → always "Invest" | Both → random mix.
account_type_lookup = users_df.set_index("User_ID")["Account_Type"].to_dict()
tx_account_types    = pd.Series(tx_user_ids).map(account_type_lookup)
both_mask           = tx_account_types == "Both"
tx_products_col     = tx_account_types.copy()
tx_products_col[both_mask] = np.random.choice(tx_products, size=int(both_mask.sum()), p=tx_product_probs)

# Assign transaction type first so amounts can match (Round-Up = small, others = larger).
tx_types_assigned = np.random.choice(tx_types, size=NUM_TRANSACTIONS, p=tx_type_probs)
is_roundup = tx_types_assigned == "Round-Up"

amounts = np.where(
    is_roundup, # Condition: is this transaction a Round-Up?
    np.random.uniform(0.01, 3.00, NUM_TRANSACTIONS),  # Round-Up: spare change between $0.01 and $3.00
    np.random.uniform(5.00, 250.00, NUM_TRANSACTIONS) # Other: deposit or withdrawal between $5.00 and $250.00
).round(2) # Round every amount to 2 decimal places so values resemble dollars and cents

# Make withdrawal amounts negative — required for correct balance calculations in SQL (a $50 withdrawal should reduce balance by $50, not increase it).
is_withdrawal = tx_types_assigned == "Withdrawal"
amounts = np.where(is_withdrawal, -amounts, amounts)

transactions_df = pd.DataFrame({
    # Transaction ID sequence from 1 to NUM_TRANSACTIONS
    "Transaction_ID":   range(1, NUM_TRANSACTIONS + 1),
    # User ID linked to each transaction
    "User_ID":          tx_user_ids,
    # Transaction date; named Transaction_Date to avoid SQL reserved keyword conflicts
    "Transaction_Date": tx_dates,
    # Transaction amounts in USD
    "Amount_USD":       amounts,
    # Transaction type, with Round-Up amounts kept small via amount assignment logic
    "Transaction_Type": tx_types_assigned,
    # Product reflects the user's Account_Type and preserves banking/invest constraints
    "Product":          tx_products_col.values,
})

# Compute Round_Up only for Round-Up transactions.
# Withdrawals and deposits should not have a round-up value.
transactions_df["Round_Up"] = np.where(
    transactions_df["Transaction_Type"] == "Round-Up",
    (np.ceil(transactions_df["Amount_USD"]) - transactions_df["Amount_USD"]).round(2),
    0.0
)

# Example output - ASCII format
# +----------------+---------+------------------+------------+------------------+---------+----------+
# | Transaction_ID | User_ID | Transaction_Date | Amount_USD | Transaction_Type | Product | Round_Up |
# +----------------+---------+------------------+------------+------------------+---------+----------+
# |              1 |    1042 | 2025-07-14       |       2.37 | Round-Up         | Banking |     0.63 |
# |              2 |    1187 | 2025-11-03       |      47.50 | Recurring Deposit| Invest  |     0.00 |
# |              3 |    1042 | 2026-01-22       |       1.15 | Round-Up         | Banking |     0.85 |
# |              4 |    1301 | 2025-09-08       |     120.00 | One-Time Deposit | Invest  |     0.00 |
# |              5 |    1187 | 2025-12-30       |     -78.43 | Withdrawal       | Banking |     0.00 |
# +----------------+---------+------------------+------------+------------------+---------+----------+

print("\n── Transactions ────────────────────────")

# Print the first five transactions without the DataFrame index
print(transactions_df.head(5).to_string(index=False))


# ─────────────────────────────────────────
# Table 3 — events
# Generate the event activity table for analytics.
# ─────────────────────────────────────────

# Assign a user ID to each event
ev_user_ids = np.random.choice(user_ids, size=NUM_EVENTS)

# Vectorized date generation using .map() — faster than list.
ev_start_dates = pd.Series(ev_user_ids).map(signup_lookup)
# Cap each event to that user's activity_end_date (disengaged users stop early).
ev_end_dates   = pd.Series(ev_user_ids).map(activity_end_lookup)
ev_days_avail  = ((ev_end_dates - ev_start_dates).dt.days).clip(lower=1)
ev_offsets     = (np.random.uniform(0, 1, NUM_EVENTS) * ev_days_avail).astype(int)
ev_dates       = ev_start_dates + pd.to_timedelta(ev_offsets, unit="D")

# Event types and their sampling probabilities.
event_types      = ["Login", "Deposit", "Withdrawal", "View_Portfolio", "View_Statement"]
event_type_probs = [0.40, 0.25, 0.10, 0.15, 0.10]

# Platform types and their sampling probabilities.
platform = ["iOS", "Android", "Web"]
platform_type_probs = [0.50, 0.35, 0.15]
assert abs(sum(event_type_probs)    - 1.0) < 1e-6, "event_type_probs must sum to 1"
assert abs(sum(platform_type_probs) - 1.0) < 1e-6, "platform_type_probs must sum to 1"

events_df = pd.DataFrame({

    # Event ID sequence from 1 to NUM_EVENTS
    "Event_ID":   range(1, NUM_EVENTS + 1),
    # User ID linked to each event
    "User_ID":    ev_user_ids,
    # Event timestamp
    "Event_Date": ev_dates,
    # Event type assigned from the event_types distribution
    "Event_Type": np.random.choice(event_types, size=NUM_EVENTS, p=event_type_probs),
    # Platform assigned from the platform distribution
    "Platform":   np.random.choice(platform, size=NUM_EVENTS, p=platform_type_probs),
    "Session_Duration_Sec": np.random.randint(10, 600, size=NUM_EVENTS),
})

# Example output - ASCII format
# +----------+---------+------------+----------------+---------+----------------------+
# | Event_ID | User_ID | Event_Date | Event_Type     | Platform| Session_Duration_Sec |
# +----------+---------+------------+----------------+---------+----------------------+
# |        1 |    1302 | 2025-08-11 | Login          | iOS     |                  243 |
# |        2 |    1087 | 2025-10-04 | Deposit        | Android |                   87 |
# |        3 |    1302 | 2026-02-17 | View_Portfolio | iOS     |                  412 |
# |        4 |    1455 | 2025-06-29 | Login          | Web     |                   35 |
# |        5 |    1087 | 2025-11-14 | Withdrawal     | Android |                  178 |
# +----------+---------+------------+----------------+---------+----------------------+

print("\n── Events ──────────────────────────────")

# Print the first five events without the DataFrame index
print(events_df.head(5).to_string(index=False))

# ─────────────────────────────────────────
# Explicit churn events — Cancel_Account
# ─────────────────────────────────────────
# Add explicit Cancel_Account events for a subset of churn-eligible users.
# These rows improve analytical realism and support downstream churn segmentation in dbt SQL.
# The final churn labels are derived later in the transformation layer (/dbt); Cancel_Account only signals intentional account closure, not the final churn status.

# Identify churn-eligible users
_last_tx_early = (
    transactions_df.groupby("User_ID")["Transaction_Date"]
    .max()
    .rename("Last_Transaction_Date")
    .reset_index()
)

# Build lookup for each user's last transaction date.
_churned_mask = _last_tx_early["Last_Transaction_Date"] < CHURN_CUTOFF
_churned_user_ids = _last_tx_early.loc[_churned_mask, "User_ID"].values
_last_tx_date_lookup = _last_tx_early.set_index("User_ID")["Last_Transaction_Date"].to_dict()

# Randomly select 30% of churned users to receive an explicit Cancel_Account event
np.random.seed(99)  # separate seed so explicit churn selection is independent
_n_explicit = max(1, int(len(_churned_user_ids) * 0.30))
_explicit_churner_ids = np.random.choice(_churned_user_ids, size=_n_explicit, replace=False)

# Build Cancel_Account events for explicit churners (subset of churn-eligible users), dated on their last transaction
_cancel_events = pd.DataFrame({
    "Event_ID":             range(NUM_EVENTS + 1, NUM_EVENTS + 1 + len(_explicit_churner_ids)),
    "User_ID":              _explicit_churner_ids,
    "Event_Date":           [_last_tx_date_lookup[uid] for uid in _explicit_churner_ids],
    "Event_Type":           "Cancel_Account",
    "Platform":             np.random.choice(platform, size=len(_explicit_churner_ids), p=platform_type_probs),
    "Session_Duration_Sec": np.random.randint(10, 120, size=len(_explicit_churner_ids)),
})

# Append Cancel_Account rows to the events table
events_df = pd.concat([events_df, _cancel_events], ignore_index=True)

# Store explicit churner IDs for downstream reference
explicit_churner_ids = set(_explicit_churner_ids)

# Print a summary of explicit Cancel_Account events added
print(f"\n── Explicit Churn Events ───────────────")
print(f"  Cancel_Account events added: {len(_cancel_events)} ({_n_explicit} users flagged as explicit churners)")

# ─────────────────────────────────────────
# Export to CSV
# ─────────────────────────────────────────
# Write each DataFrame to CSV with date-only formatting for easy SQL/Tableau ingestion.

def write_csv(df: pd.DataFrame, filename: str) -> None:
    path = OUTPUT_DIR / filename
    try:
        df.to_csv(path, index=False, date_format="%Y-%m-%d")
    except OSError as exc:
        raise RuntimeError(f"Unable to write output file {path}: {exc}") from exc

write_csv(users_df, "users.csv")
write_csv(transactions_df, "transactions.csv")
write_csv(events_df, "events.csv")

# Export generated tables and print file summaries.
print(f"\n── Exported ────────────────────────────")
print(f"  {OUTPUT_DIR}/users.csv         ({len(users_df)} rows)")
print(f"  {OUTPUT_DIR}/transactions.csv  ({len(transactions_df)} rows)")
print(f"  {OUTPUT_DIR}/events.csv        ({len(events_df)} rows)")
