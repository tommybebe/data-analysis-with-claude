#!/usr/bin/env bash
# Module 3 validation script
# Performs functional verification of permission orchestration completion.
# Usage: bash scripts/validate.sh
# Output: Korean-language validation results table

# Note: no set -e; individual checks handle errors gracefully
set -uo pipefail

# ============================================================
# Common validation functions (duplicated per module for standalone independence)
# ============================================================

MODULE_NAME="모듈 3"
MODULE_TITLE="권한 오케스트레이션"
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
    echo "🎉 ${MODULE_NAME} 완료! 모듈 4(종단간 통합)로 진행하세요."
  elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "${MODULE_NAME} 기본 완료. ⚠️ 경고 항목을 확인하세요."
  else
    echo "❌ ${FAILED_CHECKS}개 항목이 실패했습니다. 위 상세 내용을 참고하여 수정하세요."
  fi
}

# ============================================================
# Module 3 specific checks
# ============================================================

echo "🔍 ${MODULE_NAME} (${MODULE_TITLE}) 검증을 시작합니다..."
echo ""

# --- Check 0: permissions.allow and permissions.deny rules ---
if check_file_exists .claude/settings.json && check_json_valid .claude/settings.json; then
  perm_check=$(python3 -c "
import json
d = json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
allow_count = len(p.get('allow', []))
deny_count = len(p.get('deny', []))
print(f'{allow_count}|{deny_count}')" 2>/dev/null || echo "0|0")
  allow_n=$(echo "$perm_check" | cut -d'|' -f1)
  deny_n=$(echo "$perm_check" | cut -d'|' -f2)
  if [ "$allow_n" -ge 3 ] && [ "$deny_n" -ge 3 ]; then
    record_result 0 "권한 규칙 수량" "✅" "allow: ${allow_n}개, deny: ${deny_n}개"
  else
    record_result 0 "권한 규칙 수량" "❌" "allow: ${allow_n}개(최소 3), deny: ${deny_n}개(최소 3) 필요"
  fi
else
  record_result 0 "권한 규칙 수량" "❌" "settings.json 없거나 JSON 오류"
fi

# --- Check 1: Required deny rules ---
if check_file_exists .claude/settings.json && check_json_valid .claude/settings.json; then
  deny_detail=$(python3 -c "
import json
d = json.load(open('.claude/settings.json'))
deny = d.get('permissions', {}).get('deny', [])
required = ['git push --force', 'bq rm', 'rm -rf']
results = []
for r in required:
    found = any(r in item for item in deny)
    results.append(f'{r}:{\"ok\" if found else \"missing\"}')
print('|'.join(results))" 2>/dev/null || echo "error")
  if echo "$deny_detail" | grep -q "missing"; then
    missing=$(echo "$deny_detail" | tr '|' '\n' | grep "missing" | cut -d: -f1 | tr '\n' ', ')
    record_result 1 "필수 deny 규칙" "❌" "누락: ${missing}"
  else
    record_result 1 "필수 deny 규칙" "✅" "git push --force, bq rm, rm -rf 모두 포함"
  fi
else
  record_result 1 "필수 deny 규칙" "❌" "settings.json 확인 불가"
fi

# --- Check 2: GitHub Actions workflow ---
if check_file_exists .github/workflows/auto-analyze.yml; then
  # Functional check: validate YAML syntax using Python
  yaml_valid=$(python3 -c "
import yaml, sys
try:
    with open('.github/workflows/auto-analyze.yml') as f:
        data = yaml.safe_load(f)
    if data is None:
        print('empty')
    else:
        print('valid')
except yaml.YAMLError as e:
    print('invalid')
except ImportError:
    print('no_yaml')
" 2>/dev/null || echo "no_yaml")

  has_perms=$(grep -q 'permissions:' .github/workflows/auto-analyze.yml && echo "yes" || echo "no")
  has_issues_write=$(grep -q 'issues: write' .github/workflows/auto-analyze.yml && echo "yes" || echo "no")
  has_contents_write=$(grep -q 'contents: write' .github/workflows/auto-analyze.yml && echo "yes" || echo "no")

  if [ "$yaml_valid" = "invalid" ]; then
    record_result 2 "GitHub Actions 워크플로" "❌" "YAML 문법 오류 — 들여쓰기 및 구문 확인"
  elif [ "$has_perms" = "yes" ] && [ "$has_issues_write" = "yes" ] && [ "$has_contents_write" = "yes" ]; then
    record_result 2 "GitHub Actions 워크플로" "✅" "auto-analyze.yml YAML 유효 + permissions 섹션 확인"
  else
    missing=""
    [ "$has_perms" = "no" ] && missing+="permissions: "
    [ "$has_issues_write" = "no" ] && missing+="issues:write "
    [ "$has_contents_write" = "no" ] && missing+="contents:write "
    record_result 2 "GitHub Actions 워크플로" "❌" "누락: ${missing}"
  fi
else
  record_result 2 "GitHub Actions 워크플로" "❌" ".github/workflows/auto-analyze.yml 없음"
fi

# --- Check 3: Permissions rationale document ---
if check_file_exists evidence/module-3-permissions-rationale.md; then
  keyword_check=$(python3 -c "
t = open('evidence/module-3-permissions-rationale.md').read()
keywords = ['로컬', 'CI', 'GitHub Actions']
count = sum(1 for k in keywords if k in t)
print(count)" 2>/dev/null || echo "0")
  if [ "$keyword_check" -ge 2 ]; then
    record_result 3 "권한 설계 근거 문서" "✅" "로컬 vs CI 비교 내용 포함 (키워드 ${keyword_check}개)"
  else
    record_result 3 "권한 설계 근거 문서" "❌" "로컬/CI/GitHub Actions 키워드 ${keyword_check}개 — 최소 2개 필요"
  fi
else
  record_result 3 "권한 설계 근거 문서" "❌" "evidence/module-3-permissions-rationale.md 없음"
fi

# --- Check 4: Retrospective ---
if check_file_exists evidence/module-3-permissions-retrospective.md; then
  content_len=$(wc -c < evidence/module-3-permissions-retrospective.md)
  if [ "$content_len" -gt 50 ]; then
    record_result 4 "회고 기록" "✅" "module-3-permissions-retrospective.md 작성 완료"
  else
    record_result 4 "회고 기록" "❌" "내용이 너무 짧음 — 권한 설계 판단 기준 분석 작성"
  fi
else
  record_result 4 "회고 기록" "❌" "evidence/module-3-permissions-retrospective.md 없음"
fi

# --- Check 5: Environment variables ---
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
  record_result 5 "환경 변수" "❌" ".env 파일 없음 — cp .env.example .env 후 값 입력"
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
    record_result 5 "환경 변수" "✅" "GCP_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, GITHUB_REPOSITORY 설정 완료"
  else
    record_result 5 "환경 변수" "❌" "누락/오류: ${env_issues[*]}"
  fi
fi

print_results
