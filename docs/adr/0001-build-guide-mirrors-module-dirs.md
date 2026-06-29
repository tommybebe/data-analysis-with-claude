# 1. `build-guide.md` mirrors the `module-*/` directories; module dirs are the single source of truth

- **Status:** Accepted
- **Date:** 2026-06-28
- **Deciders:** Course maintainers (PR #1 — `restructure/split-course-spec`)

## Context and drivers

The course originally shipped one large `course-spec.md` that tried to be three things at once:
a syllabus (WHAT/WHY), a step-by-step build walkthrough (HOW), and an **embedded copy of the
harness source code** (hook scripts, `settings.json`, slash-command bodies, GitHub Actions).

That made `course-spec.md` a *third* copy of the harness source — alongside (1) the runnable files
under `module-*/.claude/…` and `.github/workflows/`, and (2) the prose in `instructor-setup-guide.md`.
Three copies of the same code is a three-way drift hazard, and it had already drifted: the spec
embedded **Korean-commented** versions of the hooks and command bodies while the real files on disk
use **English structural comments**, and at least two real bugs (SQL-literal truncation and
dry-run byte parsing in the cost guard) existed *only* in the spec's stale copy, never in the
runnable scripts. `AGENTS.md` had even codified the trap. A learner or maintainer reading the spec
could not tell which copy was authoritative.

We needed a single, unambiguous source of truth for the harness code, and a documentation layout
where the teaching material cannot silently contradict the code that actually runs.

## Options considered

### Option A — Keep `course-spec.md` authoritative, with embedded code

The spec remains the canonical place to read the hooks/commands/settings, and the `module-*/`
files are treated as generated/derived copies for learners to run.

- **Pros:** One document to read end to end; no need to cross-reference module dirs while learning.
- **Cons:** The authoritative copy is *not the code that runs* — it can't be executed, linted, or
  tested, so it drifts from reality by default (exactly what happened). Inverts the natural
  source-of-truth (runnable files) and makes every code change require a manual spec edit. Rejected.

### Option B — Module dirs authoritative; `build-guide.md` reproduces them **verbatim** (chosen)

Split the monolith: `course-spec.md` keeps only WHAT/WHY (objectives, concepts, self-checks);
a new `build-guide.md` holds the HOW (walkthrough + a reference reproduction of the harness code).
The `module-*/` files are the single source of truth, and every "reference" code block in
`build-guide.md` is a **byte-for-byte copy** of its real counterpart (minus the per-module
`Frozen snapshot from Module N output …` provenance line).

- **Pros:** The authoritative copy is the code that actually runs (executable, lintable, testable).
  Teaching material lives next to, but never above, the source. Verbatim reproduction means
  faithfulness is *mechanically checkable* (see ADR consequences + the committed check script).
  Low tooling cost; readers still get a single narrative document.
- **Cons:** `build-guide.md` is a hand-maintained copy, so it can re-drift if someone edits a module
  file without re-copying. Mitigated — not eliminated — by the faithfulness check.

### Option C — Generate `build-guide.md` from the module files at build time

Keep only the prose in a template and splice the real files in via a generator/preprocessor so the
code blocks are never hand-copied.

- **Pros:** Drift becomes structurally impossible; the code blocks are always current by construction.
- **Cons:** Adds a build step and a generator to a course repo that otherwise has none; contributors
  must run/understand the generator to edit docs; the rendered artifact must still be committed for
  GitHub viewing, reintroducing a checked-in copy. Heavier than the problem warrants today.

## Decision

Adopt **Option B**. The `module-*/` directories (`.claude/hooks/`, `.claude/commands/`,
`.claude/settings.json`, `.github/workflows/`, `.claude/prompts/`) are the **single source of
truth**. `build-guide.md` reproduces those files **verbatim** as a reference — identical logic and
comment language — omitting only each copy's per-module `Frozen snapshot from Module N output …`
provenance line. `course-spec.md` is demoted to WHAT/WHY and links out to `build-guide.md` and the
module dirs instead of embedding code. Clearly-labeled teaching-only examples (the empty
`settings.json` skeleton, incremental hook snippets, `/hello`, permission excerpts) are exempt
because they have no 1:1 source file.

## Consequences

- **Positive:** One authoritative, runnable copy of the harness. `course-spec.md` can no longer
  contradict the code. Faithfulness is now a property that can be asserted automatically.
- **Accepted downside:** Because `build-guide.md`'s reference blocks are a hand-maintained copy,
  they **can silently re-drift** from the module files when a module file changes and the copy is
  not updated. We accept this risk because it is mitigated by
  `scripts/check-build-guide-faithfulness.sh` — a committed, re-runnable check that fails (nonzero)
  on any drift between a claimed-verbatim block and its source file, suitable for use as a CI gate.
  We chose this mitigation over Option C's generator to keep the repo generator-free.
- **Cost to reverse:** Low-to-moderate and mechanical. Reversing to Option A means re-embedding the
  code into `course-spec.md` and re-pointing `AGENTS.md`; moving to Option C means writing a
  generator and a render step and wiring it into CI. Either way the content already lives in the
  module dirs, so no information would be lost — only the layout and the maintenance workflow change.

## References

- PR #1 (`restructure/split-course-spec`) and `reconciliation-note.md`
- `scripts/check-build-guide-faithfulness.sh` — the anti-drift gate that enforces this decision
- `AGENTS.md` → "Editing Rules" (build-guide / module-dir source-of-truth convention)
