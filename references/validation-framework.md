# Validation Framework Reference

This document describes the shared validation infrastructure used across all course modules.

## Architecture

Each module implements a two-layer validation system:

```
┌──────────────────────────────────────────┐
│  .claude/commands/validate.md            │  ← Claude Code slash command (Korean)
│  - Triggers bash scripts/validate.sh     │
│  - Interprets results for learner        │
│  - Provides remediation guidance         │
└─────────────────┬────────────────────────┘
                  │ runs
┌─────────────────▼────────────────────────┐
│  scripts/validate.sh                     │  ← Automated shell script (standalone)
│  - Common helper functions               │
│  - Module-specific checks                │
│  - Korean table output                   │
└──────────────────────────────────────────┘
```

### Layer 1: Claude Code Slash Command (`/validate`)

File: `.claude/commands/validate.md`

When a learner types `/validate` in Claude Code, this markdown file instructs Claude to:
1. Execute `bash scripts/validate.sh`
2. Present the output to the learner
3. For any failed items, provide **specific remediation steps** in Korean
4. Fall back to manual per-check execution if the script is unavailable

### Layer 2: Validation Shell Script

File: `scripts/validate.sh`

A self-contained bash script that performs actual functional verification. Can be run independently without Claude Code: `bash scripts/validate.sh`

## Common Validation Functions

Each module's `scripts/validate.sh` includes a duplicated copy of these common functions for standalone independence (no cross-module references):

```bash
# --- Module identity ---
MODULE_NAME="모듈 N"
MODULE_TITLE="module title in Korean"

# --- Result tracking ---
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNED_CHECKS=0
FAILED_CHECKS=0

declare -a CHECK_NUMS=()
declare -a CHECK_NAMES=()
declare -a CHECK_RESULTS=()
declare -a CHECK_DETAILS=()

# --- Core functions ---
record_result()         # Record a check result (num, name, ✅/❌/⚠️, detail)
check_file_exists()     # Test file existence
check_dir_exists()      # Test directory existence
check_command_available() # Test CLI command availability
check_json_valid()      # Validate JSON file syntax via python3
check_env_var()         # Read env var value from .env file (Module 0 only)
print_results()         # Output Korean-language results table with summary
```

### Output Format

All modules produce consistent Korean-language table output:

```
## 모듈 N 검증 결과 (모듈 제목)

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | check name | ✅/❌/⚠️ | details |
| ... | ... | ... | ... |

총: N/M 항목 통과

🎉 모듈 N 완료! 다음 모듈로 진행하세요.
```

### Result Categories

- ✅ Pass — check succeeded
- ⚠️ Warning — non-critical issue, module considered basically complete
- ❌ Fail — must be resolved before module completion

### Completion Message Pattern

Each module's `print_results()` includes the appropriate next-step message:

| Module | Completion Message |
|--------|-------------------|
| 0 | "🎉 모듈 0 완료! 모듈 1(훅 설정)로 진행할 준비가 되었습니다." |
| 1 | "🎉 모듈 1 완료! 모듈 2(슬래시 커맨드)로 진행하세요." |
| 2 | "🎉 모듈 2 완료! 모듈 3(권한 오케스트레이션)으로 진행하세요." |
| 3 | "🎉 모듈 3 완료! 모듈 4(종단간 통합)로 진행하세요." |
| 4 | "🎉 모듈 4 완료! 코스 전체를 성공적으로 완료했습니다. 축하합니다!" |

## Module-Specific Checks

### Module 0 — Project Setup (9 checks)
Functional verification of environment setup: env vars, CLI tools, authentication, package managers, BigQuery data load, dbt build+test.

### Module 1 — Hooks (6 checks)
Functional verification of hook configuration: settings.json structure, hook script permissions, **actual hook execution tests** (cost guard blocking, dbt error detection), deny rules, retrospective.

### Module 2 — Slash Commands (6 checks)
Content verification of slash command files: file existence with structural sections, semantic content analysis of each command (analyze, check-cost, validate-models, generate-report), retrospective.

### Module 3 — Orchestration (5 checks)
Permission policy verification: allow/deny rule counts, required deny patterns, GitHub Actions workflow structure, permissions rationale document, retrospective.

### Module 4 — Error Handling (7 checks)
End-to-end integration verification: workflow YAML validity, 7-stage label branching, error handling logic, prompt files, prompt content depth, full harness integration (hooks + permissions + commands + models), retrospective.

## Design Principles

1. **Functional over structural**: Checks verify actual behavior (running hooks, testing dbt) not just file existence
2. **Korean output**: All user-facing messages and table headers in Korean
3. **English code**: Shell script comments, variable names, and function names in English
4. **Standalone**: Each module's validate.sh runs independently with no cross-module dependencies
5. **Graceful degradation**: validate.md provides manual fallback if scripts fail
6. **Progressive depth**: Later modules verify more complex integration scenarios
