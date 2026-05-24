# FinSim - Customer Retention & Churn Data Pipeline

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)

## Key Features
- End-to-end data pipeline: synthetic data generation, transformation, and analytics
- Modern data stack: Python, DuckDB, dbt, Tableau, Amplitude
- Automated data validation and testing
- GitHub Pages documentation and interactive analysis

**[Click Here to view the final FinSim Analysis](docs/index.md)**



**Portfolio Project - Data Engineering & Analytics**

**Tech Stack:** Python · DuckDB · dbt (data build tool) · Tableau Public · Amplitude

---

## Project Overview
This repository houses a simulated, end-to-end data pipeline emulating the analytics architecture of a modern FinTech company (like Acorns). It demonstrates proficiency in raw data generation, data warehousing, SQL transformations (using dbt), and data visualization.

While the **[FinSim Analysis](docs/index.md)** focuses on product insights and A/B testing, this README serves as the technical documentation for the data pipeline.

## Repository Structure

```text
fin_sim/
├── docs/                  # GitHub Pages docs source and presentation assets
├── data/                  # Raw generated CSVs
├── dbt/                   # dbt project directory (models, tests, schema)
│   ├── models/
│   │   ├── staging/       # Staging views (stg_users, stg_events, etc.)
│   │   └── marts/         # Aggregated business logic (mart_user_summary, etc.)
│   └── dbt_project.yml
├── exports/               # Final transformed CSVs exported for Tableau ingestion
├── pipeline/              # Python pipeline scripts and helpers
│   ├── run_pipeline.py      # Automation helper for running the end-to-end pipeline
│   ├── fin_sim_data.py       # Synthetic data generator (Users, Transactions, Events)
│   ├── load_duckdb.py        # Loads raw CSVs from /data into DuckDB
│   ├── export_marts.py       # Exports dbt mart tables to /exports as CSVs
│   ├── review_data.py        # Data validation and QA script
│   └── amplitude_ingest.py   # API integration to push events into Amplitude
└── README.md                 # Technical documentation (You are here)
```

## Data Architecture & DAG

The pipeline is built on a **Modern Data Stack** architecture, mirroring enterprise Databricks/Delta Lake environments but scaled down using DuckDB for local execution.

1. **Extraction / Generation:** `fin_sim_data.py` generates synthetic, highly-relational data for 500 users, including Weibull-distributed behavior to mimic realistic decay curves and churn, saving them to `data/` as CSVs.
2. **Loading:** `load_duckdb.py` ingests the raw CSVs into a local columnar database (`dbt/dbt.duckdb`).
3. **Transformation (dbt):** 
   - **Staging (stg_):** Cleans dates, standardizes enums, and handles nulls.
   - **Marts (mart_):** Computes complex behavioral flags using SQL `CASE` expressions and date math (e.g., `days_since_last_transaction > 90` to evaluate churn logic) and aggregates data into wide tables optimized for BI tools.
4. **Export / Serving:** `export_marts.py` materializes the views back into CSVs inside the `exports/` folder for Tableau ingestion.

## Local Setup & Execution Guide

To replicate this pipeline locally, follow these steps.


**Prerequisites:**
- Python 3.10+
- `pip install pandas numpy duckdb dbt-core dbt-duckdb requests`

**Step-by-Step Execution (Windows/PowerShell):**

```powershell

# 1. Generate the raw synthetic data (outputs to data/)
py pipeline/fin_sim_data.py


# 2. Load the raw data into the DuckDB data warehouse
py pipeline/load_duckdb.py


# 3. Transform the data using dbt
cd dbt
dbt build                      # Run and test all staging and mart models
dbt docs generate              # (Optional) Generate dbt data dictionary
cd ..


# 4. Export the transformed data for visualization (outputs to exports/)
py pipeline/export_marts.py


# 5. Validate the outputs against expected business logic
py pipeline/review_data.py


# Alternative: run the full pipeline in one command
py pipeline/run_pipeline.py
```


> **Note:** `run_pipeline.py` is an automation helper for convenience. It should be used to execute the workflow, but each stage still requires independent review of logs, dbt build output, and exported results before accepting the run.

```powershell
# 6. (Optional) Sync data into Amplitude for Product Analytics
$env:AMPLITUDE_API_KEY = "your_key_here"
py pipeline/amplitude_ingest.py
```

*Note: On macOS/Linux, replace `py` with `python3`.*

## Data Modeling Notes (dbt)

*   **Churn Taxonomy:** The `mart_user_summary` model calculates a two-dimensional churn flag (Active, Silent, Explicit) based on a 90-day transaction inactivity window and `Cancel_Account` events.
*   **Testing:** Run `dbt test` within the `dbt` directory to execute 20 unique schema and custom data tests, validating data integrity (e.g., primary keys, referential integrity, and correct cohort distributions).


## Platform Limitations & Ingestion Notes
This project is architected as a local-first version of an enterprise Databricks stack. Users and reviewers should be aware of the following constraints inherent to the free-tier tools used:

*   **Tableau Public (Connectivity Restrictions)**
    Unlike a production instance of Tableau Desktop or Server, Tableau Public does not support live ODBC/JDBC drivers.
    *   *The Workaround:* The script `export_marts.py` is included to materialize dbt mart tables into CSV format.
    *   *Enterprise Mapping:* In an enterprise production environment, this extraction step would be eliminated. The dbt-transformed tables would live natively in Databricks/Delta Lake, with Tableau querying them via a direct live connection.

*   **Amplitude Free Tier (365-Day Data Window)**
    Amplitude's free tier enforces a strict 365-day rolling window for data ingestion and visibility.
    *   *The Impact:* Events with timestamps older than one year from the current date will be dropped or hidden by the Amplitude API.
    *   *Technical Requirement:* The synthetic data generator (`fin_sim_data.py`) uses a `SIM_END` variable to anchor the 12-month simulation. To ensure successful ingestion when running this repository, you must update `SIM_END` to the current date to ensure all generated event timestamps fall within the 365-day Amplitude ingestion boundary.



## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License.
See the [LICENSE](LICENSE) file for details.
