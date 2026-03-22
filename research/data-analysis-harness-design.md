# Harness Engineering for Data Analysis

This note translates the OpenAI article and Symphony repository into a practical design direction for this project's target stack:

- warehouse: BigQuery
- transforms and semantic layer: dbt
- notebook layer: marimo
- issue tracker: Linear
- git hosting: GitHub
- CI: GitHub Actions

## Working premise

For data work, harness engineering should make it easy for an agent to do useful analysis without guessing:

- what tables mean
- which environments are safe
- how to validate a metric change
- how to prove that an analysis is complete
- when to stop and ask a human

The harness should reduce ambiguity before adding more autonomy.

## Recommended repository responsibilities

The repository should become the operating manual for agent-driven analysis work. At minimum it should contain:

- `AGENTS.md` with repo rules and workflow conventions
- `WORKFLOW.md` for issue-driven execution
- data contracts for key sources and marts
- dbt model conventions and validation requirements
- notebook conventions for marimo apps and outputs
- report templates
- verification checklists for common task types
- cleanup rules for stale artifacts and low-quality patterns

## A useful mental model

There are three layers:

1. Scaffolding
2. Harness
3. Orchestration

Scaffolding is the base environment:

- repo layout
- package management with `uv`
- dbt setup
- marimo setup
- CI jobs
- secrets and environment conventions

Harness is the policy and feedback layer:

- issue templates
- `AGENTS.md`
- `WORKFLOW.md`
- tests, linters, schema checks, and runbooks
- explicit "done" criteria for analysis tasks

Orchestration is the Symphony-like loop:

- poll Linear
- create a workspace
- sync the repo
- run the right workflow
- collect proof of work
- open a PR or hand off for review

## What legibility means for data analysis

In a product codebase, legibility means clear architecture and boundaries. In a data-analysis repo, it should additionally mean:

- every important table has an owner, grain, and freshness expectation
- every metric definition is traceable to dbt models or documented SQL
- every notebook has declared inputs and outputs
- expensive queries are identifiable before execution
- local and CI validation paths are explicit
- there is a known way to render evidence for humans

If these are missing, an agent will fill gaps by guessing, which is dangerous in analytics work.

## Suggested completion evidence per issue

A data-analysis workflow should require machine-readable proof of completion, such as:

- dbt test results
- SQL validation output
- changed metric definitions with before/after explanation
- generated notebook or exported artifact
- query cost estimate or execution scope note
- links to charts, tables, or generated report files

This is the analytics equivalent of the article's emphasis on legibility and proof.

## Suggested task classes

The harness should classify tasks by automation level.

Good early candidates:

- create or update dbt models
- add tests for existing models
- produce exploratory notebooks from approved sources
- generate issue summaries and PR descriptions
- create documentation for tables, marts, and metrics

Human-gated tasks:

- destructive warehouse changes
- edits to production semantic definitions with broad business impact
- high-cost queries on large raw datasets
- changes that require business interpretation rather than technical transformation

## Proposed `WORKFLOW.md` shape for this stack

The Symphony spec suggests a strong pattern for this project:

- `tracker`: Linear project and active states
- `workspace`: per-issue local workspace root
- `hooks.after_create`: clone repo, install `uv`, fetch dbt deps
- `hooks.before_run`: sync branch, check env, confirm credentials
- `hooks.after_run`: persist logs, render summary artifacts
- `agent`: concurrency, retry, and max-turn limits
- `codex`: app-server command and sandbox policy

The Markdown body should define issue-specific instructions for analysis tasks, including:

- when BigQuery reads are allowed
- when writes are forbidden
- how dbt changes must be validated
- where marimo notebooks should live
- what artifacts must be attached before handoff

## Linear workflow suggestion

To map this to a Symphony-like control loop, use explicit states such as:

- `Todo`
- `In Progress`
- `Human Review`
- `Rework`
- `Merging`
- `Done`
- `Canceled`

The key point is not the exact labels. It is that state transitions should mean something operational for the agent.

## Continuous cleanup for a data repo

The OpenAI article's "garbage collection" idea is especially relevant for analytics, where entropy accumulates quickly. Recurring cleanup tasks could check for:

- undocumented sources
- notebooks with unclear inputs
- duplicate SQL logic
- missing dbt tests
- stale report artifacts
- drift between metric docs and model definitions

These tasks should generate small, easy-to-review PRs.

## Practical next step for this project

The most defensible sequence is:

1. Define repo scaffolding and data-task conventions.
2. Write `AGENTS.md` and `WORKFLOW.md`.
3. Make proof-of-work artifacts explicit.
4. Add validation and cleanup loops.
5. Only then add Symphony-style orchestration on top.

That ordering matches the source material: orchestration works best after the repository is already agent-legible.
