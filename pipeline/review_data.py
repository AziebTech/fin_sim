import pandas as pd
from pathlib import Path

"""Review and validate generated analytics outputs.

This module loads the exported dbt mart CSV files and raw source data,
then prints summary metrics and quality checks for the analyst.
"""

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / "exports"
DATA_DIR = BASE_DIR / "data"


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file from disk and raise a clear error if it does not exist."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def main() -> None:
    """Run review checks on exported dbt mart outputs and raw input data."""

    # Load the main analytics outputs created by dbt and exported to CSV.
    muser = load_csv(EXPORTS_DIR / "mart_user_summary.csv")
    cohort = load_csv(EXPORTS_DIR / "mart_churn_cohort.csv")
    tx = load_csv(EXPORTS_DIR / "mart_transaction_summary.csv")

    # Load raw source files for cross-checking and context.
    users = load_csv(DATA_DIR / "users.csv")
    events = load_csv(DATA_DIR / "events.csv")

    print('user total', len(muser))
    print('churn count', int(muser['churned'].sum()), 'pct', round(muser['churned'].mean() * 100, 2))
    print('churn_type counts')
    print(muser['churn_type'].value_counts(), '\n')
    print('age churn')
    print(
        muser.groupby('age_group')['churned']
        .agg(['sum', 'count'])
        .assign(pct=lambda d: (d['sum'] / d['count'] * 100).round(2))
        .sort_values('pct', ascending=False),
        '\n',
    )
    print('channel churn')
    print(
        muser.groupby('acquisition_channel')['churned']
        .agg(['sum', 'count'])
        .assign(pct=lambda d: (d['sum'] / d['count'] * 100).round(2))
        .sort_values('pct', ascending=False),
        '\n',
    )
    print('acct churn')
    print(
        muser.groupby('account_type')['churned']
        .agg(['sum', 'count'])
        .assign(pct=lambda d: (d['sum'] / d['count'] * 100).round(2))
        .sort_values('pct', ascending=False),
        '\n',
    )
    print('state churn')
    print(
        muser.groupby('state')['churned']
        .agg(['sum', 'count'])
        .assign(pct=lambda d: (d['sum'] / d['count'] * 100).round(2))
        .sort_values('pct', ascending=False)
        .head(10),
        '\n',
    )
    print('May cohort churn')
    print(
        cohort.loc[
            cohort['cohort_month'] == '2025-05-01',
            ['cohort_month', 'churn_rate_pct', 'churned_users', 'retained_users', 'total_users'],
        ],
        '\n',
    )
    print('Jul cohort churn')
    print(
        cohort.loc[
            cohort['cohort_month'] == '2025-07-01',
            ['cohort_month', 'churn_rate_pct', 'churned_users', 'retained_users', 'total_users'],
        ],
        '\n',
    )
    print('cohort rows', len(cohort))
    print('May 2026 row')
    print(
        cohort.loc[
            cohort['cohort_month'] == '2026-05-01',
            ['cohort_month', 'churn_rate_pct', 'churned_users', 'retained_users', 'total_users'],
        ],
        '\n',
    )
    print('transaction summary sample')
    print(tx.head(), '\n')
    print('transaction types by product')
    print(tx.groupby(['product', 'transaction_type'])[['transaction_count', 'net_flow']].sum(), '\n')

    user_props = users.set_index('User_ID')
    events['account_type'] = events['User_ID'].map(user_props['Account_Type'])
    print('event type counts')
    print(events['Event_Type'].value_counts(), '\n')
    for step in ['Login', 'View_Portfolio', 'Deposit']:
        print(step)
        print(events[events['Event_Type'] == step].groupby('account_type')['User_ID'].nunique(), '\n')
    login_users = events[events['Event_Type'] == 'Login'].groupby('account_type')['User_ID'].nunique()
    view_users = events[events['Event_Type'] == 'View_Portfolio'].groupby('account_type')['User_ID'].nunique()
    dep_users = events[events['Event_Type'] == 'Deposit'].groupby('account_type')['User_ID'].nunique()
    print('login view ratio')
    print((view_users / login_users * 100).round(2), '\n')
    print('login deposit ratio')
    print((dep_users / login_users * 100).round(2), '\n')
    withdraw_users = events[events['Event_Type'] == 'Withdrawal'].groupby('account_type')['User_ID'].nunique()
    print('login withdrawal ratio')
    print((withdraw_users / login_users * 100).round(2), '\n')


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
