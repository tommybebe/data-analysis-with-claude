# AGENTS.md

## Project Overview

This is the repository root for **하니스 엔지니어링 for 데이터 분석** (Harness Engineering for Data Analysis).

The course teaches agent-based data analysis automation using Claude Code and GitHub Actions.
Learners build scaffolding, skill/hook, and orchestration layers directly through the
DAU/MAU analysis sample project (BigQuery + dbt + marimo notebooks).

## Repository Structure

The course repository is organized as follows:

```
repo-root/
├── README.md                    ← Course overview and navigation (Korean)
├── AGENTS.md                    ← This file
├── course-spec.md               ← Course specification (objectives, concepts, self-checks)
├── build-guide.md               ← Build walkthrough & reference implementation (modules 1–4)
├── env-vars-manifest.md         ← Complete environment variables manifest
├── instructor-setup-guide.md    ← Instructor / self-learner setup guide
├── references/                  ← Reference documents (BigQuery, cost, data, learning cycle)
├── research/                    ← Harness engineering research notes
├── module-0-project-setup/      ← Standalone project: Environment Setup
├── module-1-hooks/              ← Standalone project: Hooks & Settings Engineering
├── module-2-slash-commands/     ← Standalone project: Slash Commands
├── module-3-orchestration/      ← Standalone project: Permission Orchestration
└── module-4-error-handling/     ← Standalone project: End-to-End Integration & Error Handling
```

Each module directory is a **self-contained working project**. Common files include
`README.md`, `CLAUDE.md`, `pyproject.toml`, and `.env.example`; later modules add
`dbt_project.yml`, `.claude/settings.json`, orchestration assets, and prerequisite snapshots.
Learners can start at any module independently.

## Documentation Conventions

- **Instructional content** (README.md, .env.example, /validate output): Korean
- **Code, variable names, file names, technical identifiers**: English
- **CLAUDE.md and code comments**: English

## Editing Rules

- `course-spec.md` is the course specification — learning objectives, key concepts, and
  self-check criteria (WHAT/WHY). Do not embed build steps or full source in it; link to
  `build-guide.md` and the module directories instead.
- `build-guide.md` holds the build walkthrough and annotated reference implementation for
  modules 1–4 (HOW). The runnable source of truth is the files under each `module-N-*/`
  directory; keep `build-guide.md` consistent with those, not the other way around.
  Its `cat > … << 'EOF'`/`'HOOKEOF'` reference blocks reproduce the module-dir files
  **verbatim** — logic and comment language included (hook scripts: English comments +
  Korean user messages; command files: English `## Input/Execution Steps/Output/Constraints`
  headers + Korean content; stage prompts: Korean headers) — omitting only each copy's
  per-module `# Frozen snapshot from Module N output …` provenance line. The empty
  `settings.json` skeleton, the incremental hook snippets, `/hello`, and the `permissions`
  excerpts are clearly-labeled teaching examples with no 1:1 source file.
  **Anti-drift gate:** run `scripts/check-build-guide-faithfulness.sh` (exit 0 = faithful,
  nonzero = drift) after editing any module file or `build-guide.md`; the rationale and the
  accepted re-drift risk are recorded in `docs/adr/0001-build-guide-mirrors-module-dirs.md`.
- `references/` documents are shared reference material duplicated into relevant modules.
- `env-vars-manifest.md` is the authoritative environment variables reference for the entire course.
- `research/` contains harness engineering research notes for course design reference.

## Environment & dbt Sharp Edges

- **Python must stay ≤ 3.12.** dbt-core 1.7–1.11 (via `mashumaro`) fails to import on
  Python 3.13+ (`UnserializableField: Field "schema" … is not serializable`). Every
  `module-*/pyproject.toml` pins `requires-python = ">=3.11,<3.13"` and ships a
  `.python-version` of `3.12` so `uv sync` never resolves a too-new interpreter. Do not
  loosen the upper bound while on dbt 1.x. `module-0`'s `scripts/validate.sh` Check 4
  asserts the venv Python is < 3.13.
- **dbt-bigquery `+schema:` concatenates, it does not replace.** With the default
  `generate_schema_name`, a folder-level `+schema: X` in `dbt_project.yml` materializes
  models into dataset `<profile.dataset>_X` (e.g. `analytics_analytics`), not `X`. Leave
  `+schema` off so models land in the profile's `dataset`, unless you deliberately want the
  concatenated dataset name.
- **Local dev auth is oauth/ADC; CI is a service-account keyfile.** For local dbt use
  `method: oauth` (`gcloud auth application-default login`, no keyfile). The
  service-account keyfile path (`GOOGLE_APPLICATION_CREDENTIALS`) is the module-4 CI route.
  `validate.sh` Check 0 accepts either.

## Prohibited

- Do not include production data or real API keys in examples.
- BigQuery queries must use the **on-demand pricing model** (no flat-rate/edition patterns).
