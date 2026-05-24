import duckdb
from pathlib import Path

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "dbt" / "dbt.duckdb"
EXPORT_DIR = BASE_DIR / "exports"
if not DB_PATH.exists():
    raise FileNotFoundError(f"DuckDB database not found: {DB_PATH}")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# Export each mart table to CSV
# ─────────────────────────────────────────

con = duckdb.connect(str(DB_PATH))

marts = [
    "mart_user_summary",
    "mart_churn_cohort",
    "mart_churn_cohort_stacked",
    "mart_transaction_summary",
]

for mart in marts:
    export_path = EXPORT_DIR / f"{mart}.csv"
    try:
        df = con.execute(f"SELECT * FROM {mart}").df()
    except duckdb.Error as exc:
        raise RuntimeError(f"Failed to export '{mart}': {exc}") from exc
    df.to_csv(export_path, index=False)
    print(f"  Exported {mart:30s} ({len(df)} rows) → {export_path}")

con.close()
print("\n── Done")