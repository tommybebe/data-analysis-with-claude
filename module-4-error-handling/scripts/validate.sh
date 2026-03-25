#!/usr/bin/env bash
# Module 4 validation script
# Performs functional verification of end-to-end integration completion.
# Usage: bash scripts/validate.sh
# Output: Korean-language validation results table

# Note: no set -e; individual checks handle errors gracefully
set -uo pipefail

# ============================================================
# Common validation functions (duplicated per module for standalone independence)
# ============================================================

MODULE_NAME="모듈 4"
MODULE_TITLE="종단간 통합"
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNED_CHECKS=0
FAILED_CHECKS=0

declare -a CHECK_NUMS=()
declare -a CHECK_NAMES=()
declare -a CHECK_RESULTS=()
declare -a CHECK_DETAILS=()

record_result() {
  local num="$1" name="$2" result="$3" detail="$4"
  CHECK_NUMS+=("$num")
  CHECK_NAMES+=("$name")
  CHECK_RESULTS+=("$result")
  CHECK_DETAILS+=("$detail")
  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  case "$result" in
    "✅") PASSED_CHECKS=$((PASSED_CHECKS + 1)) ;;
    "⚠️") WARNED_CHECKS=$((WARNED_CHECKS + 1)) ;;
    "❌") FAILED_CHECKS=$((FAILED_CHECKS + 1)) ;;
  esac
}

check_file_exists() { [ -f "$1" ]; }
check_json_valid() { python3 -m json.tool "$1" >/dev/null 2>&1; }

print_results() {
  echo ""
  echo "## ${MODULE_NAME} 검증 결과 (${MODULE_TITLE})"
  echo ""
  echo "| # | 항목 | 결과 | 상세 |"
  echo "|---|------|------|------|"
  for i in "${!CHECK_NUMS[@]}"; do
    echo "| ${CHECK_NUMS[$i]} | ${CHECK_NAMES[$i]} | ${CHECK_RESULTS[$i]} | ${CHECK_DETAILS[$i]} |"
  done
  echo ""
  echo "총: ${PASSED_CHECKS}/${TOTAL_CHECKS} 항목 통과"
  echo ""
  if [ "$FAILED_CHECKS" -eq 0 ] && [ "$WARNED_CHECKS" -eq 0 ]; then
    echo "🎉 ${MODULE_NAME} 완료! 코스 전체를 성공적으로 완료했습니다. 축하합니다!"
  elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "${MODULE_NAME} 기본 완료. ⚠️ 경고 항목을 확인하세요."
  else
    echo "❌ ${FAILED_CHECKS}개 항목이 실패했습니다. 위 상세 내용을 참고하여 수정하세요."
  fi
}

# ============================================================
# Module 4 specific checks
# ============================================================

echo "🔍 ${MODULE_NAME} (${MODULE_TITLE}) 검증을 시작합니다..."
echo ""

# --- Check 0: GitHub Actions workflow YAML exists and valid ---
if check_file_exists .github/workflows/auto-analyze.yml; then
  yaml_valid=$(python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-analyze.yml')); print('valid')" 2>/dev/null || echo "invalid")
  if [ "$yaml_valid" = "valid" ]; then
    has_labeled=$(grep -q 'labeled' .github/workflows/auto-analyze.yml && echo "yes" || echo "no")
    has_perms=$(grep -q 'permissions:' .github/workflows/auto-analyze.yml && echo "yes" || echo "no")
    if [ "$has_labeled" = "yes" ] && [ "$has_perms" = "yes" ]; then
      record_result 0 "워크플로 YAML" "✅" "YAML 유효, issues labeled 트리거 + permissions 확인"
    else
      missing=""
      [ "$has_labeled" = "no" ] && missing+="labeled 트리거 "
      [ "$has_perms" = "no" ] && missing+="permissions 키 "
      record_result 0 "워크플로 YAML" "❌" "누락: ${missing}"
    fi
  else
    record_result 0 "워크플로 YAML" "❌" "YAML 문법 오류 — python3 -c \"import yaml; yaml.safe_load(...)\" 로 확인"
  fi
else
  record_result 0 "워크플로 YAML" "❌" ".github/workflows/auto-analyze.yml 없음"
fi

# --- Check 1: 7-stage label branching logic ---
if check_file_exists .github/workflows/auto-analyze.yml; then
  stage_check=$(python3 -c "
t = open('.github/workflows/auto-analyze.yml').read()
stages = ['stage:1-parse','stage:2-define','stage:3-deliverables','stage:4-spec','stage:5-extract','stage:6-analyze','stage:7-report']
found = [s for s in stages if s in t]
missing = [s for s in stages if s not in t]
print(f'{len(found)}|{\",\".join(missing) if missing else \"none\"}')" 2>/dev/null || echo "0|error")
  found_n=$(echo "$stage_check" | cut -d'|' -f1)
  missing_stages=$(echo "$stage_check" | cut -d'|' -f2)
  if [ "$found_n" -ge 7 ]; then
    record_result 1 "7단계 라벨 분기" "✅" "7/7 단계 라벨 모두 참조됨"
  else
    record_result 1 "7단계 라벨 분기" "❌" "${found_n}/7 단계만 — 누락: ${missing_stages}"
  fi
else
  record_result 1 "7단계 라벨 분기" "❌" "워크플로 파일 없음"
fi

# --- Check 2: Error handling logic ---
if check_file_exists .github/workflows/auto-analyze.yml; then
  err_check=$(python3 -c "
t = open('.github/workflows/auto-analyze.yml').read()
checks = ['stage:error', 'error-category']
found = sum(1 for c in checks if c in t)
print(found)" 2>/dev/null || echo "0")
  if [ "$err_check" -ge 2 ]; then
    record_result 2 "오류 처리 로직" "✅" "stage:error + error-category 키워드 포함"
  else
    record_result 2 "오류 처리 로직" "❌" "오류 처리 키워드 ${err_check}/2개만 — stage:error, error-category 추가 필요"
  fi
else
  record_result 2 "오류 처리 로직" "❌" "워크플로 파일 없음"
fi

# --- Check 3: 7 stage prompt files ---
if [ -d .claude/prompts ]; then
  prompt_check=$(python3 -c "
import os
prompts = [f'stage-{i}-{n}.md' for i,n in [(1,'parse'),(2,'define'),(3,'deliverables'),(4,'spec'),(5,'extract'),(6,'analyze'),(7,'report')]]
found = [p for p in prompts if os.path.isfile(f'.claude/prompts/{p}')]
missing = [p for p in prompts if p not in found]
print(f'{len(found)}|{\",\".join(missing) if missing else \"none\"}')" 2>/dev/null || echo "0|error")
  found_n=$(echo "$prompt_check" | cut -d'|' -f1)
  missing_prompts=$(echo "$prompt_check" | cut -d'|' -f2)
  if [ "$found_n" -ge 7 ]; then
    record_result 3 "프롬프트 파일 7개" "✅" "7/7 프롬프트 파일 존재"
  else
    record_result 3 "프롬프트 파일 7개" "❌" "${found_n}/7개만 — 누락: ${missing_prompts}"
  fi
else
  record_result 3 "프롬프트 파일 7개" "❌" ".claude/prompts/ 디렉터리 없음"
fi

# --- Check 4: Stage-5 prompt content verification ---
if check_file_exists .claude/prompts/stage-5-extract.md; then
  s5_check=$(python3 -c "
t = open('.claude/prompts/stage-5-extract.md').read()
checks = [
    '1GB' in t or '1 GB' in t or 'cost' in t.lower(),
    'dbt' in t.lower(),
    'bigquery' in t.lower() or 'bq' in t.lower()
]
print(sum(checks))" 2>/dev/null || echo "0")
  if [ "$s5_check" -ge 3 ]; then
    record_result 4 "stage-5 프롬프트 내용" "✅" "비용 제한, dbt, BigQuery 참조 모두 포함"
  else
    record_result 4 "stage-5 프롬프트 내용" "❌" "필수 내용 ${s5_check}/3개만 — 비용 제한, dbt, BigQuery 참조 필요"
  fi
else
  record_result 4 "stage-5 프롬프트 내용" "❌" "stage-5-extract.md 파일 없음"
fi

# --- Check 5: Pre-built harness component integration ---
harness_check=$(python3 -c "
import json, os
checks = []
# Hook scripts
hooks = ['bq-cost-guard.sh', 'dbt-auto-test.sh', 'stop-summary.sh']
hook_ok = all(os.path.isfile(f'.claude/hooks/{h}') for h in hooks)
checks.append(('훅 스크립트 3개', hook_ok))
# Settings.json permissions
try:
    d = json.load(open('.claude/settings.json'))
    p = d.get('permissions', {})
    perm_ok = len(p.get('allow', [])) >= 3 and len(p.get('deny', [])) >= 3
    checks.append(('권한 정책', perm_ok))
except:
    checks.append(('권한 정책', False))
# Slash commands
cmds = ['analyze.md', 'check-cost.md', 'validate-models.md', 'generate-report.md']
cmd_ok = all(os.path.isfile(f'.claude/commands/{c}') for c in cmds)
checks.append(('슬래시 커맨드 4개', cmd_ok))
# dbt models
models = ['models/staging/stg_events.sql', 'models/staging/stg_users.sql', 'models/marts/fct_daily_active_users.sql']
model_ok = all(os.path.isfile(m) for m in models)
checks.append(('dbt 모델', model_ok))
passed = sum(1 for _, ok in checks if ok)
failed_items = [n for n, ok in checks if not ok]
print(f'{passed}|{\",\".join(failed_items) if failed_items else \"none\"}')" 2>/dev/null || echo "0|error")
harness_passed=$(echo "$harness_check" | cut -d'|' -f1)
harness_failed=$(echo "$harness_check" | cut -d'|' -f2)
if [ "$harness_passed" -ge 4 ]; then
  record_result 5 "하니스 통합 점검" "✅" "훅 + 권한 + 커맨드 + dbt 모델 모두 확인"
else
  record_result 5 "하니스 통합 점검" "❌" "${harness_passed}/4 통과 — 실패: ${harness_failed}"
fi

# --- Check 6: Retrospective ---
if check_file_exists evidence/module-4-retrospective.md; then
  retro_check=$(python3 -c "
t = open('evidence/module-4-retrospective.md').read()
keywords = ['하니스', '파이프라인', '비용', 'pipeline', 'cost']
count = sum(1 for k in keywords if k in t)
print(count)" 2>/dev/null || echo "0")
  if [ "$retro_check" -ge 2 ]; then
    record_result 6 "회고 기록" "✅" "하니스/파이프라인/비용 키워드 ${retro_check}개 포함"
  else
    record_result 6 "회고 기록" "❌" "키워드 ${retro_check}개 — 하니스, 파이프라인, 비용 관련 내용 보강 필요"
  fi
else
  record_result 6 "회고 기록" "❌" "evidence/module-4-retrospective.md 없음"
fi

# --- Check 7: Environment variables ---
check_env_var() {
  # Check that an environment variable is set in .env file
  local var_name="$1"
  if [ ! -f .env ]; then
    echo "NOT_FOUND"
    return
  fi
  local val
  val=$(grep -E "^${var_name}=" .env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" | xargs)
  if [ -z "$val" ]; then
    echo "EMPTY"
  else
    echo "$val"
  fi
}

if [ ! -f .env ]; then
  record_result 7 "환경 변수" "❌" ".env 파일 없음 — cp .env.example .env 후 값 입력"
else
  env_issues=()
  gcp_val=$(check_env_var "GCP_PROJECT_ID")
  if [ "$gcp_val" = "NOT_FOUND" ] || [ "$gcp_val" = "EMPTY" ]; then
    env_issues+=("GCP_PROJECT_ID")
  fi
  cred_val=$(check_env_var "GOOGLE_APPLICATION_CREDENTIALS")
  if [ "$cred_val" = "NOT_FOUND" ] || [ "$cred_val" = "EMPTY" ]; then
    env_issues+=("GOOGLE_APPLICATION_CREDENTIALS")
  elif [ ! -f "$cred_val" ]; then
    env_issues+=("GOOGLE_APPLICATION_CREDENTIALS(경로 접근 불가: $cred_val)")
  fi
  gh_repo=$(check_env_var "GITHUB_REPOSITORY")
  if [ "$gh_repo" = "NOT_FOUND" ] || [ "$gh_repo" = "EMPTY" ]; then
    env_issues+=("GITHUB_REPOSITORY")
  fi
  if [ ${#env_issues[@]} -eq 0 ]; then
    record_result 7 "환경 변수" "✅" "GCP_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, GITHUB_REPOSITORY 설정 완료"
  else
    record_result 7 "환경 변수" "❌" "누락/오류: ${env_issues[*]}"
  fi
fi

print_results
