"""load_to_bigquery.py — Load synthetic data CSVs into BigQuery.

Frozen snapshot from Module 0 output (prerequisite for Module 4).
Loads raw_users.csv and raw_events.csv into BigQuery raw dataset.

Usage:
    uv run python scripts/load_to_bigquery.py

Environment variables:
    GCP_PROJECT_ID                  Google Cloud project ID (required)
    GOOGLE_APPLICATION_CREDENTIALS  Path to service account JSON key (required)
    BQ_DATASET_RAW                  Raw dataset name (default: raw)
    DATASET_LOCATION                Dataset location (default: US)
"""

import os

import pandas as pd
from google.cloud import bigquery

# Configuration via environment variables
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET_RAW = os.environ.get("BQ_DATASET_RAW", "raw")
LOCATION = os.environ.get("DATASET_LOCATION", "US")


def load_csv_to_bigquery(client: bigquery.Client, csv_path: str, table_id: str) -> None:
    """Load a CSV file into a BigQuery table."""
    df = pd.read_csv(csv_path)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )

    full_table_id = f"{PROJECT_ID}.{DATASET_RAW}.{table_id}"
    print(f"Loading {csv_path} → {full_table_id} ({len(df)} rows)...")

    job = client.load_table_from_dataframe(df, full_table_id, job_config=job_config)
    job.result()  # Wait for completion

    table = client.get_table(full_table_id)
    print(f"  ✅ Loaded {table.num_rows} rows to {full_table_id}")


if __name__ == "__main__":
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Create dataset if not exists
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_RAW)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {DATASET_RAW} exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        client.create_dataset(dataset)
        print(f"Created dataset {DATASET_RAW}")

    # Load CSVs
    load_csv_to_bigquery(client, "data/raw_users.csv", "raw_users")
    load_csv_to_bigquery(client, "data/raw_events.csv", "raw_events")
    print("✅ All data loaded successfully")
