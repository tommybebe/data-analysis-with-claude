# CLAUDE.md — Module 3: Permissions Orchestration

This file provides Claude Code with project context for Module 3 of the Harness Engineering
for Data Analysis course. Module 3 teaches permissions orchestration — designing agent boundaries
for local development and CI/CD pipeline environments.

## Project Overview

This is a **DAU/MAU analysis project** for FitTrack, a B2C mobile fitness app. The tech stack:
- **BigQuery** (on-demand pricing) as the data warehouse
- **dbt** (dbt-bigquery adapter) for data transformations
- **marimo** for analysis notebooks
- **GitHub Actions** for CI/CD automation
- **Claude Code** as the AI coding agent

## Module 3 Scope

Module 3 builds the permissions orchestration layer on top of Module 0's data infrastructure,
Module 1's hook-based policy enforcement, and Module 2's slash command specifications. The data
pipeline, hooks, and slash commands are already established as frozen prerequisites. Learners:
1. Explore the Claude Code permission model (global, project, local scopes)
2. Design allow rules for data analysis agent — minimum required permissions
3. Implement deny rules for irreversible operations and verify blocking behavior
4. Design GitHub Actions `permissions:` keys for CI environment separation
5. Compare local vs CI multi-environment permission policies
6. Test permission boundaries end-to-end and write retrospective

## Project Structure

```
module-3-orchestration/
├── CLAUDE.md                 # This file — agent instructions
├── AGENTS.md                 # Agent rules (Module 0 prerequisite)
├── README.md                 # Korean-language instructional content
├── pyproject.toml            # Python dependencies
├── dbt_project.yml           # dbt project configuration (Module 0 prerequisite)
├── packages.yml              # dbt packages (Module 0 prerequisite)
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
├── profiles.yml.example      # dbt connection config template
├── models/                   # dbt models (Module 0 prerequisite — frozen)
│   ├── staging/
│   │   ├── sources.yml       # BigQuery source declarations
│   │   ├── stg_events.sql    # Event cleansing and timezone normalization
│   │   ├── stg_users.sql     # User profile normalization
│   │   └── schema.yml        # Staging model tests
│   └── marts/
│       ├── fct_daily_active_users.sql    # DAU aggregation
│       ├── fct_monthly_active_users.sql  # MAU aggregation
│       ├── fct_retention_cohort.sql      # Cohort retention
│       └── schema.yml                    # Mart model tests
├── scripts/                  # Data generation scripts (Module 0 prerequisite)
│   ├── generate_synthetic_data.py
│   └── load_to_bigquery.py
├── .claude/                  # Claude Code harness configuration
│   ├── settings.json         # Hook + permissions config (Module 1 prerequisite)
│   ├── hooks/                # Hook scripts (Module 1 prerequisite)
│   │   ├── bq-cost-guard.sh      # PreToolUse — BigQuery cost guard
│   │   ├── dbt-auto-test.sh      # PostToolUse — dbt compile verification
│   │   └── stop-summary.sh       # Stop — session summary generation
│   └── commands/             # Slash commands
│       ├── validate.md       # /validate command (provided)
│       ├── analyze.md        # /analyze command (Module 2 prerequisite)
│       ├── check-cost.md     # /check-cost command (Module 2 prerequisite)
│       ├── validate-models.md  # /validate-models command (Module 2 prerequisite)
│       └── generate-report.md  # /generate-report command (Module 2 prerequisite)
├── .github/                  # GitHub Actions (reference template — not executable from subdir)
│   └── workflows/
│       └── auto-analyze.yml  # Learner creates: CI/CD workflow with permissions
├── analyses/                 # marimo notebooks (learner-created output)
└── evidence/                 # Validation artifacts (learner-created output)
    ├── module-3-permissions-rationale.md     # Learner creates: permission design rationale
    └── module-3-permissions-retrospective.md # Learner creates: retrospective
```

## Frozen Prerequisites (from Module 0)

The following files are pre-built outputs from Module 0. They form the working data pipeline.
Do NOT modify these unless instructed:
- `dbt_project.yml`, `packages.yml` — dbt project configuration
- `models/staging/*` — Staging models and source declarations
- `models/marts/*` — Mart models (DAU, MAU, retention)
- `scripts/*` — Synthetic data generation and BigQuery loading
- `AGENTS.md` — Declarative agent rules

## Frozen Prerequisites (from Module 1)

The following files are pre-built outputs from Module 1. They form the hook-based policy layer.
Do NOT modify these unless instructed:
- `.claude/hooks/bq-cost-guard.sh` — PreToolUse BigQuery cost guard
- `.claude/hooks/dbt-auto-test.sh` — PostToolUse dbt compile verification
- `.claude/hooks/stop-summary.sh` — Stop session summary generation

## Frozen Prerequisites (from Module 2)

The following files are pre-built outputs from Module 2. They form the slash command layer.
Do NOT modify these unless instructed:
- `.claude/commands/analyze.md` — Full analysis workflow specification
- `.claude/commands/check-cost.md` — BigQuery cost estimation command
- `.claude/commands/validate-models.md` — dbt model validation command
- `.claude/commands/generate-report.md` — Report generation command

## What Learners Modify and Create in Module 3

### Learner modifies (enhancing existing configuration)
- `.claude/settings.json` — Add comprehensive `permissions.allow` (≥3 rules) and
  `permissions.deny` (≥3 rules) sections for data analysis agent boundaries

### Learner creates from scratch
- `.github/workflows/auto-analyze.yml` — GitHub Actions workflow with `permissions:` keys
  (draft or complete version; full implementation in Module 4)
- `evidence/module-3-permissions-rationale.md` — Permission design rationale document
  (local vs CI comparison, allow/deny rule justifications)
- `evidence/module-3-permissions-retrospective.md` — Module retrospective

## Environment Variables

All environment-specific values use environment variables. Never hardcode project IDs,
dataset names, or file paths.

### Required
- `GCP_PROJECT_ID` — Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS` — Absolute path to GCP service account JSON key file
- `GITHUB_REPOSITORY` — GitHub repository path (owner/repo format)

### Optional (have defaults)
- `BQ_DATASET_RAW` — Raw data dataset name (default: `raw`)
- `BQ_DATASET_ANALYTICS` — Analytics dataset name (default: `analytics`)
- `DATASET_LOCATION` — BigQuery dataset location (default: `US`)
- `BQ_COST_LIMIT_BYTES` — BigQuery cost guard threshold in bytes (default: `1073741824` = 1GB)

### CI-only (GitHub Secrets)
- `CLAUDE_TOKEN` — Claude authentication token for GitHub Actions (not needed locally)

## Key Constraints

- **BigQuery pricing**: Always use on-demand pricing model; never use flat-rate/edition patterns
- **Partition filters**: Always include partition filters in BigQuery queries
- **No full-refresh**: Do not run `dbt run --full-refresh` without explicit user instruction
- **No destructive operations**: Never run `rm -rf`, `DROP TABLE`, `DELETE FROM`, or `TRUNCATE`
  without user confirmation
- **Security**: Never commit service account JSON keys or `profiles.yml` to the repository
- **Cost awareness**: Estimate BigQuery scan costs before running queries
  (on-demand: $5/TB scanned)

## Hook Engineering Concepts (from Module 1)

### Hook Types
- **PreToolUse**: Runs BEFORE a tool executes; exit 1 cancels the tool execution
- **PostToolUse**: Runs AFTER a tool executes; exit 1 reports error but execution already complete
- **Stop**: Runs when Claude Code session ends; for observability and cleanup

### Matcher Patterns
- `"Bash"` — Matches all Bash tool invocations (broad)
- `"Bash(bq query*)"` — Matches only bq query commands (scoped)
- `"Edit(models/**/*.sql)"` — Matches SQL model file edits (scoped)
- Matchers control hook activation scope; too broad = false positives, too narrow = gaps

### Hook Exit Codes
- `exit 0` — Allow / success — Claude Code continues
- `exit 1` — Block / failure — Claude Code stops (PreToolUse cancels, PostToolUse reports error)

## Slash Command Concepts (from Module 2)

### Command File Format
Slash commands are Markdown files in `.claude/commands/`. Each file defines a structured task
specification that Claude Code follows when the user invokes `/command-name`.

### $ARGUMENTS Variable
`$ARGUMENTS` is dynamically replaced with user input after the command name.
Example: `/analyze 2026년 1월 DAU` → `$ARGUMENTS = "2026년 1월 DAU"`

### Command Design Principles
- Each command should have clear Input, Execution Steps, Output, and Constraints sections
- Commands should leverage existing hooks (cost guard activates automatically on bq queries)
- Evidence files (JSON) provide machine-verifiable proof of command execution
- Commands should be composable — designed to chain sequentially

## Permissions Orchestration Concepts

### Claude Code Permission Scopes
Permissions are applied at three scope levels, with more specific scopes taking priority:
1. **Global** (`~/.claude/settings.json`) — All Claude Code sessions
2. **Project** (`.claude/settings.json`) — This repository only (primary focus)
3. **Local** (`.claude/settings.local.json`) — Individual developer overrides (gitignored)

### Permission Rule Syntax
- `permissions.allow` — Whitelist of allowed tool invocations (e.g., `Bash(dbt run:*)`)
- `permissions.deny` — Blacklist of blocked tool invocations (e.g., `Bash(git push --force:*)`)
- Priority: `deny` > `allow` — deny rules always take precedence

### GitHub Actions `permissions:` Keys
GitHub Actions permissions control GitHub API access for workflows:
- `issues: write` — Issue comments and label management
- `contents: write` — File commits and branch push
- `pull-requests: write` — PR creation and description

### Local vs CI Permission Design
- **Local development**: More permissive for interactive exploration
- **CI pipeline**: Stricter — no human supervision, automated execution
- **Shared deny rules**: Irreversible operations blocked in both environments

## dbt Conventions

- Source declarations in `models/staging/sources.yml` using `env_var()` for dataset references
- Staging models: `stg_<entity>.sql` — cleansing, type casting, timezone normalization
- Mart models: `fct_<metric>.sql` — business logic, aggregation
- All models documented and tested in `schema.yml`
- Use `{{ env_var('GCP_PROJECT_ID') }}` and `{{ env_var('BQ_DATASET_RAW') }}` in dbt configs

## marimo Conventions

- Notebook files in `analyses/` directory
- File naming: `analysis_[metric]_[YYYYMM].py` (e.g., `analysis_dau_202601.py`)
- marimo notebooks are Python files — use `marimo edit` to open in browser
- Export to HTML with `marimo export html` for reports
