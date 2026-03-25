# AGENTS.md

## Project Overview

This is the course overview directory for **하니스 엔지니어링 for 데이터 분석** (Harness Engineering for Data Analysis).

The course teaches agent-based data analysis automation using Claude Code and GitHub Actions.
Learners build scaffolding, skill/hook, and orchestration layers directly through the
DAU/MAU analysis sample project (BigQuery + dbt + marimo notebooks).

## Repository Structure

The course repository is organized as follows:

```
repo-root/
├── initialize/                  ← You are here (course overview)
│   ├── README.md                ← Course overview and navigation (Korean)
│   ├── AGENTS.md                ← This file
│   ├── course-spec.md           ← Full course specification
│   ├── env-vars-manifest.md     ← Complete environment variables manifest
│   ├── instructor-setup-guide.md← Instructor / self-learner setup guide
│   ├── references/              ← Reference documents (BigQuery, cost, data, learning cycle)
│   └── research/                ← Harness engineering research notes
│
├── module-0/                    ← Standalone project: Environment Setup
├── module-1/                    ← Standalone project: Hooks & Settings Engineering
├── module-2/                    ← Standalone project: Slash Commands
├── module-3/                    ← Standalone project: Permission Orchestration
└── module-4/                    ← Standalone project: End-to-End Agent Workflow
```

Each `module-N/` directory is a **fully self-contained working project** with its own
`pyproject.toml`, `dbt_project.yml`, `.claude/settings.json`, and prerequisite snapshots.
Learners can start at any module independently.

## Documentation Conventions

- **Instructional content** (README.md, .env.example, /validate output): Korean
- **Code, variable names, file names, technical identifiers**: English
- **CLAUDE.md and code comments**: English

## Editing Rules

- `course-spec.md` is the authoritative course specification. Keep it in sync with any
  changes to module content.
- `references/` documents are shared reference material duplicated into relevant modules.
- `env-vars-manifest.md` is the authoritative environment variables reference for the entire course.
- `research/` contains harness engineering research notes for course design reference.

## Prohibited

- Do not include production data or real API keys in examples.
- BigQuery queries must use the **on-demand pricing model** (no flat-rate/edition patterns).
