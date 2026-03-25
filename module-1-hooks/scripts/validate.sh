#!/usr/bin/env bash
# Module 1 validation script
# Performs functional verification of hook configuration completion.
# Usage: bash scripts/validate.sh
# Output: Korean-language validation results table

# Note: no set -e; individual checks handle errors gracefully
set -uo pipefail

# ============================================================
# Common validation functions (duplicated per module for standalone independence)
# ============================================================

MODULE_NAME="모듈 1"
MODULE_TITLE="훅 설정"
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNED_CHECKS=0
FAILED_CHECKS=0

declare -a CHECK_NUMS=()
declare -a CHECK_NAMES=()
declare -a CHECK_RESULTS=()
declare -a CHECK_DETAILS=()

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
check_dir_exists() { [ -d "$1" ]; }
check_command_available() { command -v "$1" >/dev/null 2>&1; }
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
    echo "🎉 ${MODULE_NAME} 완료! 모듈 2(슬래시 커맨드)로 진행하세요."
  elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "${MODULE_NAME} 기본 완료. ⚠️ 경고 항목을 확인하세요."
  else
    echo "❌ ${FAILED_CHECKS}개 항목이 실패했습니다. 위 상세 내용을 참고하여 수정하세요."
  fi
}

# ============================================================
# Module 1 specific checks
# ============================================================

echo "🔍 ${MODULE_NAME} (${MODULE_TITLE}) 검증을 시작합니다..."
echo ""

# --- Check 0: settings.json exists and valid JSON ---
if check_file_exists .claude/settings.json; then
  if check_json_valid .claude/settings.json; then
    has_hooks=$(python3 -c "import json; d=json.load(open('.claude/settings.json')); print('yes' if 'hooks' in d else 'no')" 2>/dev/null || echo "no")
    has_perms=$(python3 -c "import json; d=json.load(open('.claude/settings.json')); print('yes' if 'permissions' in d else 'no')" 2>/dev/null || echo "no")
    if [ "$has_hooks" = "yes" ] && [ "$has_perms" = "yes" ]; then
      record_result 0 "settings.json 구조" "✅" "JSON 유효, hooks + permissions 키 존재"
    else
      missing=""
      [ "$has_hooks" = "no" ] && missing+="hooks "
      [ "$has_perms" = "no" ] && missing+="permissions "
      record_result 0 "settings.json 구조" "❌" "누락된 키: ${missing}"
    fi
  else
    record_result 0 "settings.json 구조" "❌" "JSON 문법 오류 — trailing comma, 따옴표 확인"
  fi
else
  record_result 0 "settings.json 구조" "❌" ".claude/settings.json 파일 없음"
fi

# --- Check 1: Hook script permissions ---
hooks=("bq-cost-guard.sh" "dbt-auto-test.sh" "stop-summary.sh")
all_executable=true
missing_hooks=()
for h in "${hooks[@]}"; do
  if [ ! -f ".claude/hooks/$h" ]; then
    all_executable=false
    missing_hooks+=("$h(없음)")
  elif [ ! -x ".claude/hooks/$h" ]; then
    all_executable=false
    missing_hooks+=("$h(실행권한 없음)")
  fi
done
if $all_executable; then
  record_result 1 "훅 스크립트 실행 권한" "✅" "3개 파일 모두 실행 가능"
else
  record_result 1 "훅 스크립트 실행 권한" "❌" "문제: ${missing_hooks[*]} — chmod +x .claude/hooks/*.sh"
fi

# --- Check 2: Cost guard hook blocking test ---
# Functional test: set BQ_COST_LIMIT_BYTES=1 so any query exceeds the limit,
# then verify the hook exits non-zero (blocks the query).
if check_file_exists .claude/hooks/bq-cost-guard.sh; then
  if [ -x .claude/hooks/bq-cost-guard.sh ]; then
    test_input='{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}'
    test_exit=0
    test_out=$(echo "$test_input" | BQ_COST_LIMIT_BYTES=1 bash .claude/hooks/bq-cost-guard.sh 2>&1) || test_exit=$?
    if [ "$test_exit" -ne 0 ]; then
      record_result 2 "비용 가드 차단 동작" "✅" "COST_LIMIT=1 byte → exit ${test_exit} (차단 확인)"
    elif echo "$test_out" | grep -qi "block\|차단\|exceed\|초과\|deny\|reject"; then
      record_result 2 "비용 가드 차단 동작" "✅" "COST_LIMIT=1 byte → 차단 메시지 출력 확인"
    else
      record_result 2 "비용 가드 차단 동작" "❌" "훅이 차단하지 않음 (exit 0) — BQ_COST_LIMIT_BYTES 비교 로직 확인"
    fi
  else
    record_result 2 "비용 가드 차단 동작" "❌" "bq-cost-guard.sh 실행 권한 없음 — chmod +x .claude/hooks/bq-cost-guard.sh"
  fi
else
  record_result 2 "비용 가드 차단 동작" "❌" "bq-cost-guard.sh 파일 없음"
fi

# --- Check 3: PostToolUse dbt error detection ---
# Functional test: write intentionally broken SQL, invoke the hook,
# and verify it exits non-zero or reports an error.
if check_file_exists .claude/hooks/dbt-auto-test.sh && check_command_available uv; then
  if [ -x .claude/hooks/dbt-auto-test.sh ]; then
    # Create a broken SQL file temporarily
    mkdir -p models/marts 2>/dev/null
    echo "SELEC * FORM broken_table_xyz" > models/marts/_test_broken_validate.sql
    test_input='{"tool_name":"Write","tool_input":{"file_path":"models/marts/_test_broken_validate.sql"}}'
    dbt_hook_exit=0
    dbt_hook_out=$(echo "$test_input" | bash .claude/hooks/dbt-auto-test.sh 2>&1) || dbt_hook_exit=$?
    rm -f models/marts/_test_broken_validate.sql
    if [ "$dbt_hook_exit" -ne 0 ]; then
      record_result 3 "dbt 오류 감지 훅" "✅" "잘못된 SQL → exit ${dbt_hook_exit} (오류 감지 확인)"
    elif echo "$dbt_hook_out" | grep -qi "fail\|error\|compilation\|컴파일"; then
      record_result 3 "dbt 오류 감지 훅" "✅" "잘못된 SQL → 오류 메시지 출력 확인"
    else
      record_result 3 "dbt 오류 감지 훅" "⚠️" "dbt compile 검증은 profiles.yml 설정 후 정확히 동작"
    fi
  else
    record_result 3 "dbt 오류 감지 훅" "❌" "dbt-auto-test.sh 실행 권한 없음 — chmod +x .claude/hooks/dbt-auto-test.sh"
  fi
else
  if ! check_file_exists .claude/hooks/dbt-auto-test.sh; then
    record_result 3 "dbt 오류 감지 훅" "❌" "dbt-auto-test.sh 파일 없음"
  else
    record_result 3 "dbt 오류 감지 훅" "⚠️" "uv 미설치 — dbt compile 테스트 건너뜀"
  fi
fi

# --- Check 4: permissions.deny patterns ---
if check_file_exists .claude/settings.json && check_json_valid .claude/settings.json; then
  deny_check=$(python3 -c "
import json
d = json.load(open('.claude/settings.json'))
deny = d.get('permissions', {}).get('deny', [])
required = ['git push --force', 'bq rm', 'dbt run --full-refresh', 'rm -rf']
found = [r for r in required if any(r in item for item in deny)]
missing = [r for r in required if r not in found]
print(f'{len(found)}|{\"|\".join(missing) if missing else \"none\"}')" 2>/dev/null || echo "0|error")
  found_count=$(echo "$deny_check" | cut -d'|' -f1)
  missing_patterns=$(echo "$deny_check" | cut -d'|' -f2-)
  if [ "$found_count" -ge 4 ]; then
    record_result 4 "permissions.deny 규칙" "✅" "필수 차단 패턴 ${found_count}개 확인"
  else
    record_result 4 "permissions.deny 규칙" "❌" "누락 패턴: ${missing_patterns}"
  fi
else
  record_result 4 "permissions.deny 규칙" "❌" "settings.json 없거나 JSON 오류"
fi

# --- Check 5: Retrospective ---
if check_file_exists evidence/module-1-retrospective.md; then
  content_len=$(wc -c < evidence/module-1-retrospective.md)
  if [ "$content_len" -gt 50 ]; then
    record_result 5 "회고 기록" "✅" "module-1-retrospective.md 작성 완료"
  else
    record_result 5 "회고 기록" "❌" "내용이 너무 짧음 — 훅 vs permissions 비교 분석 작성"
  fi
else
  record_result 5 "회고 기록" "❌" "evidence/module-1-retrospective.md 없음"
fi

# --- Check 6: Environment variables ---
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
  record_result 6 "환경 변수" "❌" ".env 파일 없음 — cp .env.example .env 후 값 입력"
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
  if [ ${#env_issues[@]} -eq 0 ]; then
    record_result 6 "환경 변수" "✅" "GCP_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS 설정 완료"
  else
    record_result 6 "환경 변수" "❌" "누락/오류: ${env_issues[*]}"
  fi
fi

print_results
