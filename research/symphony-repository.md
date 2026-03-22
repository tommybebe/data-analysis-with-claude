# Symphony Repository Notes

Sources:

- https://github.com/openai/symphony
- https://github.com/openai/symphony/blob/main/SPEC.md
- https://github.com/openai/symphony/blob/main/elixir/README.md

## What Symphony is

Symphony is an orchestration service for agent work. Its purpose is to turn issue execution into a repeatable, long-running workflow rather than a manual "open a ticket and babysit the agent" process.

The repo description is concise:

- Symphony turns project work into isolated, autonomous implementation runs.
- Teams manage work instead of supervising coding agents.

The README also states that Symphony works best after a codebase has already adopted harness engineering.

## Important scope boundary

The spec defines Symphony as:

- a scheduler and runner
- a reader of issue-tracker state
- a coordinator of isolated workspaces and agent sessions

It is not primarily:

- a full control plane
- a general workflow engine
- a built-in business-logic layer for ticket updates and PR handling

The spec is explicit that many ticket writes are expected to be performed by the agent itself through tools available in the runtime.

## Core architecture from the spec

The draft v1 spec breaks Symphony into a small set of layers:

- Workflow Loader
- Config Layer
- Issue Tracker Client
- Orchestrator
- Workspace Manager
- Agent Runner
- Logging
- optional Status Surface

This layering matters because it shows what OpenAI considers portable. The implementation language is secondary; the workflow contract and orchestration boundaries are the important parts.

## The central repo contract: `WORKFLOW.md`

One of the most important ideas in the spec is that runtime behavior lives in a repository-owned `WORKFLOW.md` file. This file contains:

- YAML front matter for configuration
- Markdown body for the agent prompt template

The front matter can define:

- tracker settings
- polling cadence
- workspace root
- lifecycle hooks
- agent concurrency and retry settings
- Codex app-server launch configuration

This is a concrete example of repository knowledge becoming the system of record. The policy and workflow live beside the code they govern.

## Operational behavior

From the spec and Elixir README, the standard workflow is:

1. Poll Linear for candidate issues.
2. Create or reuse one workspace per issue.
3. Launch Codex in app-server mode inside that workspace.
4. Render a prompt from `WORKFLOW.md` plus issue metadata.
5. Keep the agent working until the issue is done, paused, or moved out of an active state.
6. Retry on transient failure with backoff.
7. Clean up workspaces when issues reach terminal states.

The spec also emphasizes:

- bounded concurrency
- restart recovery without a database
- structured logs
- operator-visible observability

## Why workspace isolation matters

Per-issue workspaces are a practical harness choice. They give:

- containment of side effects
- reproducible local context
- simpler cleanup
- clearer debugging
- a natural boundary for sandbox and policy decisions

This is the implementation counterpart to the article's broader idea of legibility.

## What the Elixir reference implementation adds

The Elixir README makes the prototype more concrete:

- it polls Linear
- it launches Codex app-server in the issue workspace
- it can expose a `linear_graphql` client-side tool
- it can run a Phoenix dashboard for observability
- it supports a configurable `WORKFLOW.md`
- it includes live end-to-end tests, including optional SSH worker scenarios

The README also includes an explicit warning:

- the Elixir implementation is prototype software for evaluation
- teams are encouraged to build their own hardened implementation from the spec

That warning matters. OpenAI is publishing the architecture and reference pattern more than a production-ready product.

## Relationship to harness engineering

Symphony operationalizes several ideas from the article:

- In-repo workflow definition: `WORKFLOW.md` acts as versioned policy.
- Explicit control plane: Linear issue states become agent routing signals.
- Isolation: each issue gets its own workspace.
- Observability: logs and optional dashboards make runs inspectable.
- Continuity: retries, reconciliation, and cleanup make agent work service-like instead of ad hoc.

In other words, harness engineering prepares the repository. Symphony sits on top of that harness to automate project execution.

## Limitations and caveats

The repo repeatedly signals caution:

- trusted environments are assumed
- approval and sandbox posture are implementation-defined
- strong safety controls are not mandated by the spec
- the reference implementation is intentionally low-key and experimental

This means Symphony should not be copied blindly into a production environment without additional hardening, especially around credentials, destructive actions, and costly workloads.

## What is most relevant for a data-analysis setup

The most reusable Symphony ideas for this project are:

- use the issue tracker as the orchestration surface
- isolate work per issue in separate workspaces
- store workflow policy in-repo
- make bootstrapping repeatable through hooks
- make completion criteria machine-checkable
- keep observability and cleanup built into the workflow, not as an afterthought
