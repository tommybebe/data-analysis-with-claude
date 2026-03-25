# CLAUDE.md — Module 4: End-to-End Integration & Error Handling

This file provides Claude Code with project context for Module 4 of the Harness Engineering
for Data Analysis course. Module 4 teaches end-to-end pipeline integration — combining all
harness components (hooks, slash commands, permissions) into a GitHub Actions 7-stage workflow
with error handling and recovery.

## Project Overview

This is a **DAU/MAU analysis project** for FitTrack, a B2C mobile fitness app. The tech stack:
- **BigQuery** (on-demand pricing) as the data warehouse
- **dbt** (dbt-bigquery adapter) for data transformations
- **marimo** for analysis notebooks
- **GitHub Actions** for CI/CD automation
- **Claude Code** as the AI coding agent

## Module 4 Scope

Module 4 is the capstone module that integrates all harness components from Modules 0-3 into
a fully automated end-to-end data analysis pipeline. The data pipeline, hooks, slash commands,
and permissions are all established as frozen prerequisites. Learners:
1. Verify all harness components from Modules 1-3 are correctly configured
2. Write a GitHub Actions 7-stage orchestration workflow YAML
3. Design 7 agent prompt files for stage-based pipeline execution
4. Execute the full pipeline end-to-end (issue → PR with analysis report)
5. Practice intentional error injection and `stage:error` label-based recovery
6. Measure pipeline costs and write a retrospective

## Project Structure

```
module-4-error-handling/
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
│   ├── settings.json         # Hook + permissions config (Module 1+3 prerequisite)
│   ├── hooks/                # Hook scripts (Module 1 prerequisite)
│   │   ├── bq-cost-guard.sh      # PreToolUse — BigQuery cost guard
│   │   ├── dbt-auto-test.sh      # PostToolUse — dbt compile verification
│   │   └── stop-summary.sh       # Stop — session summary generation
│   ├── commands/             # Slash commands (Module 2 prerequisite)
│   │   ├── validate.md       # /validate command (provided)
│   │   ├── analyze.md        # /analyze command (Module 2 prerequisite)
│   │   ├── check-cost.md     # /check-cost command (Module 2 prerequisite)
│   │   ├── validate-models.md  # /validate-models command (Module 2 prerequisite)
│   │   └── generate-report.md  # /generate-report command (Module 2 prerequisite)
│   └── prompts/              # Pipeline stage prompts (learner-created)
│       ├── stage-1-parse.md       # Learner creates: issue parsing prompt
│       ├── stage-2-define.md      # Learner creates: problem definition prompt
│       ├── stage-3-deliverables.md  # Learner creates: deliverables spec prompt
│       ├── stage-4-spec.md        # Learner creates: analysis spec prompt
│       ├── stage-5-extract.md     # Learner creates: data extraction prompt
│       ├── stage-6-analyze.md     # Learner creates: analysis execution prompt
│       └── stage-7-report.md      # Learner creates: report generation prompt
├── .github/                  # GitHub Actions (reference template — not executable from subdir)
│   └── workflows/
│       └── auto-analyze.yml  # Learner creates: 7-stage orchestration workflow
├── analyses/                 # marimo notebooks (learner-created output)
└── evidence/                 # Validation artifacts (learner-created output)
    ├── query_cost_log.json           # Learner creates: BigQuery cost log
    └── module-4-retrospective.md     # Learner creates: retrospective
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

## Frozen Prerequisites (from Module 3)

The following files are pre-built outputs from Module 3. They form the permissions layer.
Do NOT modify these unless instructed:
- `.claude/settings.json` — Comprehensive permissions.allow (≥3 rules) and permissions.deny
  (≥3 rules) for agent boundary enforcement, plus hook registrations

## What Learners Modify and Create in Module 4

### Learner creates from scratch
- `.github/workflows/auto-analyze.yml` — GitHub Actions 7-stage orchestration workflow
  with label chaining, error handling, and artifact uploads
- `.claude/prompts/stage-1-parse.md` through `stage-7-report.md` — 7 agent prompt files
  for each pipeline stage
- `evidence/query_cost_log.json` — BigQuery cost log from pipeline execution
- `evidence/module-4-retrospective.md` — Pipeline execution retrospective
  (harness integration effects, pipeline stability, BigQuery cost measurement)

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
- `GCP_SA_KEY` — GCP service account key JSON (base64 encoded, for CI authentication)

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

## Permissions Orchestration Concepts (from Module 3)

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

## 7-Stage Pipeline Architecture

### Label Chaining Mechanism
Each stage completion triggers the next via GitHub Issues label swap:
1. `auto-analyze` → `stage:1-parse` → ... → `stage:7-report` → `done`
2. On error: current label replaced with `stage:error` + error comment with category anchor
3. Recovery: remove `stage:error`, re-attach failed stage label to resume

### Error Categories
| Category | Code | Example | Auto-retry |
|----------|------|---------|------------|
| Infrastructure | `INFRA` | BigQuery auth failure, GitHub API rate limit | Yes (max 3) |
| Data | `DATA` | Table not found, dbt test failure | No (data fix needed) |
| Agent | `AGENT` | Invalid SQL, marimo execution error | Yes (max 2, with prompt reinforcement) |
| Workflow | `WORKFLOW` | Label transition failure, permissions missing | No (workflow fix needed) |

### Stage Prompt Design Principles
- Each prompt in `.claude/prompts/stage-N-*.md` receives context from prior stage comments
- Stage 5 (extract) is the most cost-sensitive — enforce 1GB scan limit
- Stage 7 (report) must include `evidence/` file links in PR body for traceability

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

## GitHub Actions Workflow Conventions

- Workflow file: `.github/workflows/auto-analyze.yml`
- Trigger: `on.issues.types: [labeled]`
- Required permissions: `issues: write`, `contents: write`, `pull-requests: write`
- Stage completion anchors in issue comments: `<!-- stage:N-complete -->`
- Error anchors: `<!-- error-category: INFRA|DATA|AGENT|WORKFLOW -->`
- Artifact uploads for HTML/PDF reports
