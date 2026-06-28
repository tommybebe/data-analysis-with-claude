# Reconciliation Note — `course-spec.md` split + `build-guide.md` ↔ module-dir reconciliation

Scope: PR #1 (`restructure/split-course-spec`). This note records (1) the verification that no
substance was lost when `course-spec.md` was split, (2) the reconciliation of every reference
code block in `build-guide.md` to its real counterpart on disk, and (3) the resolution of the two
automated-review (Codex) findings.

Baseline for all diffs: pre-split `course-spec.md` at `origin/main` (commit `e315a9e`).

---

## 1. Content preservation (pre-split `course-spec.md` → `course-spec.md` + `build-guide.md`)

Line count: pre-split `course-spec.md` = 3171 lines; post-split `course-spec.md` (1288) +
`build-guide.md` (1571) = 2859 lines → **net −312**, consistent with the PR's claimed ~300-line
reduction (one duplicated ~250-line learning-cycle section condensed to a pointer, plus dead
code/link removal).

### What moved where

| Pre-split section (`e315a9e`) | Now lives in | Notes |
|---|---|---|
| WHAT/WHY: 코스 개요·하니스 정의·수강 대상·코스 구조·학습 목표·모듈별 학습 목표/핵심 개념/자기 점검 체크리스트/자가 점검 | `course-spec.md` | Kept; the module `활동`/walkthrough bodies were replaced with pointers |
| HOW: 모듈 1–4 `사전 준비` + `활동` (hooks, settings.json, command bodies, permissions, GitHub Actions) + 프롬프트 예제 + 관찰-수정-창작 사이클 | `build-guide.md` | Sliced out of the spec; reference code then **reconciled** (see §2) |
| 모듈 0 `활동` walkthrough (clone, env, GCP/secrets, SDK auth, synthetic data, dbt build) | `module-0-project-setup/README.md` + `instructor-setup-guide.md` | Build-guide §모듈 0 and spec §실습 단계 are now pointers to these (more detailed than the old spec) |
| 샘플 프로젝트·평가 기준·교수자 참고·용어·참고 자료 | `course-spec.md` | Kept |

### Intentionally cut / deduped (not substance loss)

- **3단계 학습 사이클 detail (~254 lines, old `course-spec.md` 2684–2937).** Condensed in
  `course-spec.md` to a summary table + pointer to
  [`references/learning-cycle-framework.md`](references/learning-cycle-framework.md). That
  reference file already existed at `e315a9e` (32 KB, **unchanged by this PR**) and is a strict
  superset of the condensed material (pedagogical rationale, per-phase structure, transition
  criteria, application matrix, repeatability guidelines). So this is a genuine de-duplication
  against an existing canonical doc, not a deletion.
- **Dead links removed:** references to the deleted `modules/module-{0..4}.md` directory and to a
  non-existent `examples/` directory (the 산출물 목록 table now points to `build-guide.md` and
  `module-{0,1,2,3,4}-*/`).
- **Path correction (pre-existing in the PR):** module-4 integration check now uses
  `.claude/hooks/bq-cost-guard.sh` (old spec used the stale `scripts/hooks/` path).

### Genuinely dropped → restored

- **Module-0 baseline-measurement step (old `course-spec.md` 활동 7).** It is referenced as an
  expected artifact (`evidence/module-0-baseline.md`) in both the spec's self-check (점검 5/6) and
  `module-0-project-setup/CLAUDE.md`, but no step told learners how to produce it. Restored as
  **단계 8: Claude Code 레포 이해도 기준선 측정** in `module-0-project-setup/README.md`
  (the correct home — module-0 HOW lives in that README, not in `build-guide.md`, which is scoped
  to modules 1–4).

**Conclusion:** every substantive section and walkthrough step from `e315a9e` survives in
`course-spec.md`, `build-guide.md`, the module-dir READMEs, or `references/learning-cycle-framework.md`.
Nothing of substance was lost.

---

## 2. `build-guide.md` reference code reconciled to the real module files

`build-guide.md`'s code blocks had been sliced verbatim from the **old** spec, which had drifted
from the runnable files. The module directories are authoritative; each block was fixed to match
them (not the reverse). Every `cat > … << 'EOF'/'HOOKEOF'` block is now a **verbatim copy** of the
real file — logic and comment language included — omitting only each copy's per-module
`# Frozen snapshot from Module N output …` provenance line.

| build-guide block | Reconciled to | Key drift that was fixed |
|---|---|---|
| `bq-cost-guard.sh` | `module-1-hooks/.claude/hooks/bq-cost-guard.sh` | SQL truncation bug, JSON-only byte parsing bug, `exit 0`-on-parse-fail, variable/struct/message drift, English comments |
| `dbt-auto-test.sh` | `module-1-hooks/.claude/hooks/dbt-auto-test.sh` | `set -uo`→`set -euo`, `dbt compile`→`uv run dbt compile`, path-match + output-capture drift |
| `stop-summary.sh` (full) | `module-1-hooks/.claude/hooks/stop-summary.sh` | list-of-sessions model → real single-dict `session_log.json` model; timestamp format; comments |
| `settings.json` (활동 4, full) | `module-1-hooks/.claude/settings.json` (identical across all modules) | allow/deny rule set drift (invented `bq show/ls`, `uv run`, granular `gh`, extra deny rules) |
| `analyze.md` | `module-3-orchestration/.claude/commands/analyze.md` | ~100-line elaborate spec → lean real file; Korean headers → real English `## Input/...`; evidence file names |
| `check-cost.md` | `module-3-orchestration/.claude/commands/check-cost.md` | same |
| `validate-models.md` | `module-3-orchestration/.claude/commands/validate-models.md` | same |
| `generate-report.md` | `module-3-orchestration/.claude/commands/generate-report.md` | same |
| Module-3 `permissions.allow`/`.deny` examples | canonical `settings.json` | invented rules (`Bash(bq:*)`, `marimo`, `gcloud … delete`, etc.) → faithful excerpts of the real allow/deny |
| Module-3 GitHub Actions `permissions:` excerpt | `module-3-orchestration/.github/workflows/auto-analyze.yml` | `name`/job-name + top-level `permissions:` aligned to the real workflow |
| Module-4 issue creation | `module-4-error-handling/README.md` | removed reference to a **non-existent** `.github/ISSUE_TEMPLATE/analysis-request.md`; now uses the README's inline issue body |

**Already consistent (verified, no change needed):** module-4 label-creation block (11 labels,
colors, descriptions), stage-prompt structure (`## 컨텍스트/작업 지시/산출물/제약 조건`, matching
`stage-1-parse.md`), error categories (`INFRA/DATA/AGENT/WORKFLOW`), label-chaining flow,
`evidence/query_cost_log.json` cost aggregation.

**Clearly-labeled teaching examples (intentionally not 1:1 with any file):** the empty
`settings.json` skeleton (활동 1), the incremental hook snippets (활동 1–3), `/hello` (no real
command file; relabeled and converted to the real `## Input/...` header style), and the `permissions`
excerpts. The framing note at the top of `build-guide.md` was updated to describe this.

Faithfulness was verified programmatically: all 7 heredoc blocks and the full `settings.json` block
diff **clean** against the real files (minus the provenance line); the embedded `settings.json`
parses as valid JSON and equals the canonical object.

---

## 3. Automated-review (Codex) findings — resolution

Codex flagged two P2 issues in the cost guard: (a) SQL literal truncation, (b) dry-run byte parsing.

**Both bugs existed only in `build-guide.md`'s stale reference, never in the real scripts.** The real
`bq-cost-guard.sh` (in `module-1-hooks` and, identically, `module-2/3/4`) already:

- extracts the SQL **greedily between double quotes** —
  `sed -n 's/.*bq query[^"]*"\(.*\)".*/\1/p'` — so internal quotes don't truncate it (the
  build-guide reference used `sed "…;s/['\"].*//"`, which cut at the first quote); and
- parses the **first integer from the dry-run text output** —
  `grep -oP '\d+' | head -1` — rather than reading a JSON field that `bq query --dry_run` does not
  emit in text mode (the build-guide reference parsed `statistics.totalBytesProcessed` as JSON).

Therefore **no real script was changed**. The reconciliation in §2 replaces the buggy reference with
the correct real script, which resolves both findings. (A brief reply to this effect is appropriate
on PR #1.)

---

## Out-of-scope observation (not changed)

- The dataset naming differs between the **illustrative** minimal-`AGENTS.md` starter / example
  `/check-cost` commands in `build-guide.md` (`fittrack_analytics`, `fittrack_production`) and the
  real module convention (`BQ_DATASET_ANALYTICS` default `analytics`, plus `raw`). This is a
  pre-existing inconsistency in clearly-labeled teaching prose, outside the reference-code scope of
  this reconciliation; flagged here for a future pass.
