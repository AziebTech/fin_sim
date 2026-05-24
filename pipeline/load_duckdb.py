import duckdb
from pathlib import Path

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "dbt" / "dbt.duckdb"

# ─────────────────────────────────────────
# Connect to DuckDB
# ─────────────────────────────────────────

con = duckdb.connect(str(DB_PATH))

# ─────────────────────────────────────────
# Load CSVs into DuckDB tables
# ─────────────────────────────────────────

# Dictionary maps table name → CSV file name
tables = {
    "raw_users":        "users.csv",
    "raw_transactions": "transactions.csv",
    "raw_events":       "events.csv",
}


for table_name, csv_file in tables.items():
    csv_path = DATA_DIR / csv_file
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    # DROP and recreate each time so re-running this script always gives fresh data
    con.execute(f"DROP TABLE IF EXISTS {table_name}")

    # READ_CSV_AUTO lets DuckDB detect column types automatically from the file
    con.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT * FROM READ_CSV_AUTO('{csv_path.as_posix()}', header=true)
    """)

    row = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    if row is None:
        raise RuntimeError(f"Failed to retrieve row count for {table_name}")
    row_count = row[0]
    print(f"  Loaded {table_name:20s} ← {csv_file}  ({row_count} rows)")

# ─────────────────────────────────────────
# Verify — print first 3 rows of each table
# ─────────────────────────────────────────

print("\n── Preview ─────────────────────────────")
for table_name in tables:
    print(f"\n{table_name}:")
    print(con.execute(f"SELECT * FROM {table_name} LIMIT 3").df().to_string(index=False))

con.close()
print(f"\n── Done — database saved to: {DB_PATH}")