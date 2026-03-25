# FitTrack Data Analysis Agent Guide

Frozen snapshot from Module 0 output (prerequisite for Module 4).
This file provides declarative rules for the Claude Code agent.

## BigQuery Policy
- Analytics dataset: use env var `BQ_DATASET_ANALYTICS` (default: `analytics`) — read/write allowed
- Raw dataset: use env var `BQ_DATASET_RAW` (default: `raw`) — read only
- Single query scan limit: 1GB or less (exceeding requires dry-run confirmation before proceeding)
- Always use on-demand pricing model ($5/TB scanned)
- Always include partition filters in queries

## dbt Model Conventions
- Analysis queries are based on the `models/marts/` layer (`fct_*`, `dim_*`)
- New models require `unique` + `not_null` tests
- Source declarations use `env_var()` for all environment-specific values
- Staging models: `stg_<entity>.sql` — cleansing, type casting, timezone normalization
- Mart models: `fct_<metric>.sql` — business logic, aggregation

## Prohibited Actions
- `git push --force` — history corruption risk
- `bq rm`, `DROP TABLE`, `DELETE FROM` — data loss
- Queries scanning >1GB without dry-run confirmation
- `dbt run --full-refresh` without explicit instruction
- Committing service account keys or `profiles.yml`

## Environment Variables
All environment-specific values use environment variables. Never hardcode project IDs.
- `GCP_PROJECT_ID` — Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS` — Path to service account JSON key
- `BQ_DATASET_RAW` — Raw data dataset name (default: `raw`)
- `BQ_DATASET_ANALYTICS` — Analytics dataset name (default: `analytics`)
