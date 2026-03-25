# CLAUDE.md — Module 0: Project Setup

This file provides Claude Code with project context for Module 0 of the Harness Engineering
for Data Analysis course. Module 0 is the orientation and environment setup module.

## Project Overview

This is a **DAU/MAU analysis project** for FitTrack, a B2C mobile fitness app. The tech stack:
- **BigQuery** (on-demand pricing) as the data warehouse
- **dbt** (dbt-bigquery adapter) for data transformations
- **marimo** for analysis notebooks (introduced in later modules)
- **GitHub Actions** for CI/CD automation (introduced in later modules)
- **Claude Code** as the AI coding agent

## Module 0 Scope

Module 0 establishes the data infrastructure foundation. Learners:
1. Set up the local development environment (uv, dbt, marimo, Claude Code CLI)
2. Configure GCP service account and GitHub Secrets
3. Write synthetic data generation scripts and load data into BigQuery
4. Set up the dbt project and write staging + mart models
5. Run `dbt run && dbt test` to validate the pipeline

This module does NOT include harness configuration (hooks, slash commands, AGENTS.md,
permissions, workflows). Those are built in Modules 1–4.

## Project Structure

```
module-0-project-setup/
├── CLAUDE.md                 # This file — agent instructions
├── README.md                 # Korean-language instructional content
├── pyproject.toml            # Python dependencies (dbt-bigquery, data generation)
├── dbt_project.yml           # dbt project configuration (learner creates)
├── packages.yml              # dbt packages (learner creates)
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
├── profiles.yml.example      # dbt connection config template (never commit profiles.yml)
├── models/                   # dbt models (learner creates)
│   ├── staging/
│   │   ├── sources.yml       # BigQuery source declarations
│   │   ├── stg_events.sql    # Event cleansing and timezone normalization
│   │   └── stg_users.sql     # User profile normalization
│   ├── marts/
│   │   ├── fct_daily_active_users.sql    # DAU aggregation (grain: date × platform)
│   │   ├── fct_monthly_active_users.sql  # MAU aggregation (grain: month × platform)
│   │   └── fct_retention_cohort.sql      # Cohort retention (grain: cohort_month × months_since)
│   └── schema.yml            # Model documentation and tests
├── scripts/                  # Data generation scripts (learner creates)
│   ├── generate_synthetic_data.py
│   └── load_to_bigquery.py
└── evidence/                 # Learner-created validation artifacts
    └── module-0-baseline.md  # Claude Code repo understanding baseline
```

## Environment Variables

All environment-specific values use environment variables. Never hardcode project IDs,
dataset names, or file paths.

### Required
- `GCP_PROJECT_ID` — Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS` — Absolute path to GCP service account JSON key file

### Optional (have defaults)
- `BQ_DATASET_RAW` — Raw data dataset name (default: `raw`)
- `BQ_DATASET_ANALYTICS` — Analytics dataset name (default: `analytics`)
- `DATASET_LOCATION` — BigQuery dataset location (default: `US`)
- `SYNTHETIC_NUM_USERS` — Number of synthetic users (default: `10000`)
- `SYNTHETIC_START_DATE` — Synthetic data start date (default: `2026-01-01`)
- `SYNTHETIC_END_DATE` — Synthetic data end date (default: `2026-03-31`)

## Key Constraints

- **BigQuery pricing**: Always use on-demand pricing model; never use flat-rate/edition patterns
- **Partition filters**: Always include partition filters in BigQuery queries
- **No full-refresh**: Do not run `dbt run --full-refresh` without explicit user instruction
- **No destructive operations**: Never run `rm -rf`, `DROP TABLE`, `DELETE FROM`, or `TRUNCATE`
  without user confirmation
- **Security**: Never commit service account JSON keys or `profiles.yml` to the repository
- **Cost awareness**: Estimate BigQuery scan costs before running queries
  (on-demand: $5/TB scanned)

## dbt Conventions

- Source declarations in `models/staging/sources.yml` using `env_var()` for dataset references
- Staging models: `stg_<entity>.sql` — cleansing, type casting, timezone normalization
- Mart models: `fct_<metric>.sql` — business logic, aggregation
- All models documented and tested in `schema.yml`
- Use `{{ env_var('GCP_PROJECT_ID') }}` and `{{ env_var('BQ_DATASET_RAW') }}` in dbt configs

## What Learners Create vs What Is Pre-built

### Pre-built (provided in this directory)
- `pyproject.toml` — Python dependency specification
- `CLAUDE.md` — This agent instruction file
- `.env.example` — Environment variable template
- `.gitignore` — Git ignore rules

### Learner creates from scratch
- `dbt_project.yml` and `packages.yml`
- `profiles.yml` (local only, never committed)
- All dbt models (`models/staging/`, `models/marts/`, `schema.yml`)
- Data generation scripts (`scripts/`)
- `evidence/module-0-baseline.md`
