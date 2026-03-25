#!/usr/bin/env bash
# Module 2 validation script
# Performs functional verification of slash command implementation.
# Usage: bash scripts/validate.sh
# Output: Korean-language validation results table

# Note: no set -e; individual checks handle errors gracefully
set -uo pipefail

# ============================================================
# Common validation functions (duplicated per module for standalone independence)
# ============================================================

MODULE_NAME="모듈 2"
MODULE_TITLE="슬래시 커맨드"
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
    echo "🎉 ${MODULE_NAME} 완료! 모듈 3(권한 오케스트레이션)으로 진행하세요."
  elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "${MODULE_NAME} 기본 완료. ⚠️ 경고 항목을 확인하세요."
  else
    echo "❌ ${FAILED_CHECKS}개 항목이 실패했습니다. 위 상세 내용을 참고하여 수정하세요."
  fi
}

# ============================================================
# Module 2 specific checks
# ============================================================

echo "🔍 ${MODULE_NAME} (${MODULE_TITLE}) 검증을 시작합니다..."
echo ""

# --- Check 0: Slash command files exist with required sections and minimum content ---
commands=("analyze" "check-cost" "validate-models" "generate-report")
MIN_CMD_BYTES=200  # Minimum content length to be a meaningful command spec
all_present=true
all_structured=true
cmd_issues=()
for cmd in "${commands[@]}"; do
  f=".claude/commands/${cmd}.md"
  if ! check_file_exists "$f"; then
    all_present=false
    cmd_issues+=("${cmd}.md 없음")
  else
    content=$(cat "$f")
    content_len=$(wc -c < "$f")
    if [ "$content_len" -lt "$MIN_CMD_BYTES" ]; then
      all_structured=false
      cmd_issues+=("${cmd}.md: ${content_len}바이트(최소 ${MIN_CMD_BYTES})")
      continue
    fi
    missing_sections=()
    # Check for key structural sections (flexible Korean/English)
    echo "$content" | grep -qiE "(input|입력|argument)" || missing_sections+=("Input")
    echo "$content" | grep -qiE "(step|단계|절차|execution)" || missing_sections+=("Steps")
    echo "$content" | grep -qiE "(output|출력|결과)" || missing_sections+=("Output")
    if [ ${#missing_sections[@]} -gt 0 ]; then
      all_structured=false
      cmd_issues+=("${cmd}.md: ${missing_sections[*]} 섹션 누락")
    fi
  fi
done
if $all_present && $all_structured; then
  record_result 0 "슬래시 커맨드 파일" "✅" "4개 파일 존재, 필수 섹션 포함, 최소 분량 충족"
elif $all_present; then
  record_result 0 "슬래시 커맨드 파일" "⚠️" "${cmd_issues[*]}"
else
  record_result 0 "슬래시 커맨드 파일" "❌" "${cmd_issues[*]}"
fi

# --- Check 1: /analyze command structure ---
if check_file_exists .claude/commands/analyze.md; then
  content=$(cat .claude/commands/analyze.md)
  checks=0
  echo "$content" | grep -q '\$ARGUMENTS' && checks=$((checks + 1))
  echo "$content" | grep -qiE "marimo|notebook|analyses/" && checks=$((checks + 1))
  echo "$content" | grep -qiE "fct_daily_active_users|fct_monthly_active_users|dbt" && checks=$((checks + 1))
  echo "$content" | grep -qiE "cost|비용|dry.run" && checks=$((checks + 1))
  if [ "$checks" -ge 3 ]; then
    record_result 1 "/analyze 커맨드 구조" "✅" "핵심 요소 ${checks}/4개 포함"
  else
    record_result 1 "/analyze 커맨드 구조" "❌" "핵심 요소 ${checks}/4개만 포함 — \$ARGUMENTS, marimo, dbt 모델, 비용 확인 필요"
  fi
else
  record_result 1 "/analyze 커맨드 구조" "❌" "analyze.md 파일 없음"
fi

# --- Check 2: /check-cost command structure ---
if check_file_exists .claude/commands/check-cost.md; then
  content=$(cat .claude/commands/check-cost.md)
  checks=0
  echo "$content" | grep -qiE "dry.run|dry_run" && checks=$((checks + 1))
  echo "$content" | grep -qiE "byte|MB|GB" && checks=$((checks + 1))
  echo "$content" | grep -qiE "safe|warning|dangerous|안전|경고|위험|✅|⚠️|❌" && checks=$((checks + 1))
  echo "$content" | grep -qiE "query_cost_log|cost_log" && checks=$((checks + 1))
  if [ "$checks" -ge 3 ]; then
    record_result 2 "/check-cost 커맨드 구조" "✅" "핵심 요소 ${checks}/4개 포함"
  else
    record_result 2 "/check-cost 커맨드 구조" "❌" "핵심 요소 ${checks}/4개만 — dry-run, 바이트 출력, 판단 기준, 로그 저장 필요"
  fi
else
  record_result 2 "/check-cost 커맨드 구조" "❌" "check-cost.md 파일 없음"
fi

# --- Check 3: /validate-models command structure ---
if check_file_exists .claude/commands/validate-models.md; then
  content=$(cat .claude/commands/validate-models.md)
  checks=0
  echo "$content" | grep -qiE "dbt test" && checks=$((checks + 1))
  echo "$content" | grep -qiE "dbt_test_results" && checks=$((checks + 1))
  echo "$content" | grep -qiE "total_tests|passed|failed" && checks=$((checks + 1))
  if [ "$checks" -ge 2 ]; then
    record_result 3 "/validate-models 구조" "✅" "핵심 요소 ${checks}/3개 포함"
  else
    record_result 3 "/validate-models 구조" "❌" "핵심 요소 ${checks}/3개만 — dbt test, JSON 저장, 결과 필드 필요"
  fi
else
  record_result 3 "/validate-models 구조" "❌" "validate-models.md 파일 없음"
fi

# --- Check 4: /generate-report command structure ---
if check_file_exists .claude/commands/generate-report.md; then
  content=$(cat .claude/commands/generate-report.md)
  checks=0
  echo "$content" | grep -qiE "marimo|export|HTML|html" && checks=$((checks + 1))
  echo "$content" | grep -qiE "report_manifest" && checks=$((checks + 1))
  echo "$content" | grep -qiE "format|path|outputs" && checks=$((checks + 1))
  if [ "$checks" -ge 2 ]; then
    record_result 4 "/generate-report 구조" "✅" "핵심 요소 ${checks}/3개 포함"
  else
    record_result 4 "/generate-report 구조" "❌" "핵심 요소 ${checks}/3개만 — marimo export, 매니페스트, 출력 형식 필요"
  fi
else
  record_result 4 "/generate-report 구조" "❌" "generate-report.md 파일 없음"
fi

# --- Check 5: Retrospective ---
if check_file_exists evidence/module-2-retrospective.md; then
  content_len=$(wc -c < evidence/module-2-retrospective.md)
  if [ "$content_len" -gt 50 ]; then
    record_result 5 "회고 기록" "✅" "module-2-retrospective.md 작성 완료"
  else
    record_result 5 "회고 기록" "❌" "내용이 너무 짧음 — 커맨드-훅 역할 분담 분석 작성"
  fi
else
  record_result 5 "회고 기록" "❌" "evidence/module-2-retrospective.md 없음"
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
