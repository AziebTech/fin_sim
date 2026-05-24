"""Run the data pipeline in the correct end-to-end order.

This runner is an automation helper. It is intended to simplify execution,
not to replace manual review of outputs or dbt validation artifacts.
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DBT_DIR = PROJECT_ROOT / "dbt"
EXPORTS_DIR = PROJECT_ROOT / "exports"


def run_command(command, step, cwd=None):
    print(f"\n--- Running: {step} ---")
    print(f"Command: {' '.join(command)}")
    subprocess.run(command, cwd=cwd or PROJECT_ROOT, check=True)
    print(f"{step} completed successfully")


def verify_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Validation failed: {description} not found at {path}")
    print(f"Verified {description}: {path}")


def print_summary(statuses):
    print("\n=== Pipeline Status Summary ===")
    for step, status in statuses:
        print(f"- {step}: {status}")
    print("=== End of summary ===\n")


def main() -> None:
    steps = [
        ("Generate synthetic data", [sys.executable, str(BASE_DIR / "fin_sim_data.py")], None),
        ("Load raw data into DuckDB", [sys.executable, str(BASE_DIR / "load_duckdb.py")], None),
        ("Build dbt models", ["dbt", "build"], str(DBT_DIR)),
        ("Generate dbt docs", ["dbt", "docs", "generate"], str(DBT_DIR)),
        ("Export dbt outputs", [sys.executable, str(BASE_DIR / "export_marts.py")], None),
        ("Review exported results", [sys.executable, str(BASE_DIR / "review_data.py")], None),
    ]

    statuses = []

    for step_name, command, cwd in steps:
        try:
            run_command(command, step_name, cwd=cwd)

            if step_name == "Load raw data into DuckDB":
                verify_file(PROJECT_ROOT / "dbt" / "dbt.duckdb", "DuckDB warehouse file")
            elif step_name == "Build dbt models":
                verify_file(DBT_DIR / "target" / "run_results.json", "dbt build results file")
            elif step_name == "Export dbt outputs":
                for output_file in [
                    "mart_user_summary.csv",
                    "mart_churn_cohort.csv",
                    "mart_transaction_summary.csv",
                ]:
                    verify_file(EXPORTS_DIR / output_file, f"exported CSV {output_file}")

            statuses.append((step_name, "SUCCESS"))
        except subprocess.CalledProcessError as exc:
            print(f"\nERROR: {step_name} failed with exit code {exc.returncode}")
            statuses.append((step_name, "FAILED"))
            print_summary(statuses)
            sys.exit(exc.returncode)
        except Exception as exc:
            print(f"\nERROR: {step_name} encountered a validation error: {exc}")
            statuses.append((step_name, "FAILED"))
            print_summary(statuses)
            sys.exit(1)

    print_summary(statuses)
    print("Pipeline complete. Please review dbt build output and exported results before accepting the run.")
    print("To sync product analytics data to Amplitude, run:\n  py pipeline/amplitude_ingest.py")


if __name__ == "__main__":
    main()
