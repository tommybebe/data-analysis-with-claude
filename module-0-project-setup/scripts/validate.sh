#!/usr/bin/env bash
# Module 0 validation script
# Performs functional verification of project setup completion.
# Usage: bash scripts/validate.sh
# Output: Korean-language validation results table

# Note: no set -e; individual checks handle errors gracefully
set -uo pipefail

# ============================================================
# Common validation functions (duplicated per module for standalone independence)
# ============================================================

MODULE_NAME="모듈 0"
MODULE_TITLE="프로젝트 설정"
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNED_CHECKS=0
FAILED_CHECKS=0

# Result storage for table output
declare -a CHECK_NUMS=()
declare -a CHECK_NAMES=()
declare -a CHECK_RESULTS=()
declare -a CHECK_DETAILS=()

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

check_file_exists() {
  [ -f "$1" ]
}

check_dir_exists() {
  [ -d "$1" ]
}

check_command_available() {
  command -v "$1" >/dev/null 2>&1
}

check_json_valid() {
  python3 -m json.tool "$1" >/dev/null 2>&1
}

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
    echo "🎉 ${MODULE_NAME} 완료! 모듈 1(훅 설정)로 진행할 준비가 되었습니다."
  elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "${MODULE_NAME} 기본 완료. ⚠️ 경고 항목을 확인하세요."
  else
    echo "❌ ${FAILED_CHECKS}개 항목이 실패했습니다. 위 상세 내용을 참고하여 수정하세요."
  fi
}

# ============================================================
# Module 0 specific checks
# ============================================================

echo "🔍 ${MODULE_NAME} (${MODULE_TITLE}) 검증을 시작합니다..."
echo ""

# --- Check 0: Environment variables ---
if [ ! -f .env ]; then
  record_result 0 "환경 변수" "❌" ".env 파일 없음 — .env.example을 .env로 복사 후 값 입력"
else
  gcp_val=$(check_env_var "GCP_PROJECT_ID")
  cred_val=$(check_env_var "GOOGLE_APPLICATION_CREDENTIALS")
  if [ "$gcp_val" = "NOT_FOUND" ] || [ "$gcp_val" = "EMPTY" ]; then
    record_result 0 "환경 변수" "❌" "GCP_PROJECT_ID가 비어 있음"
  elif [ "$cred_val" = "NOT_FOUND" ] || [ "$cred_val" = "EMPTY" ]; then
    record_result 0 "환경 변수" "❌" "GOOGLE_APPLICATION_CREDENTIALS가 비어 있음"
  elif [ ! -f "$cred_val" ]; then
    record_result 0 "환경 변수" "⚠️" "인증 파일 경로가 존재하지 않음: $cred_val"
  else
    record_result 0 "환경 변수" "✅" "GCP_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS 설정 완료"
  fi
fi

# --- Check 1: Claude Code CLI ---
if check_command_available claude; then
  ver=$(claude --version 2>&1 | head -1)
  record_result 1 "Claude Code CLI" "✅" "$ver"
else
  record_result 1 "Claude Code CLI" "❌" "claude 명령어를 찾을 수 없음 — 설치 필요"
fi

# --- Check 2: Claude Code auth ---
if check_command_available claude; then
  whoami_out=$(claude whoami 2>&1 || true)
  if echo "$whoami_out" | grep -qiE "@|authenticated|account"; then
    record_result 2 "Claude Code 인증" "✅" "$(echo "$whoami_out" | head -1)"
  else
    record_result 2 "Claude Code 인증" "❌" "인증 필요 — claude login 실행"
  fi
else
  record_result 2 "Claude Code 인증" "❌" "Claude Code CLI 미설치"
fi

# --- Check 3: uv package manager ---
if check_command_available uv; then
  ver=$(uv --version 2>&1 | head -1)
  record_result 3 "uv 패키지 매니저" "✅" "$ver"
else
  record_result 3 "uv 패키지 매니저" "❌" "uv 미설치 — curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# --- Check 4: dbt installation ---
if check_command_available uv; then
  dbt_out=$(uv run dbt --version 2>&1 || true)
  if echo "$dbt_out" | grep -qi "dbt-core"; then
    if echo "$dbt_out" | grep -qi "bigquery"; then
      record_result 4 "dbt 설치 상태" "✅" "dbt-core + bigquery 어댑터 확인"
    else
      record_result 4 "dbt 설치 상태" "❌" "bigquery 어댑터 미설치"
    fi
  else
    record_result 4 "dbt 설치 상태" "❌" "dbt-core 미설치 — uv sync 실행"
  fi
else
  record_result 4 "dbt 설치 상태" "❌" "uv 미설치"
fi

# --- Check 5: marimo installation ---
if check_command_available uv; then
  marimo_out=$(uv run marimo --version 2>&1 || true)
  if echo "$marimo_out" | grep -qE "[0-9]+\.[0-9]+"; then
    record_result 5 "marimo 설치 상태" "✅" "$(echo "$marimo_out" | head -1)"
  else
    record_result 5 "marimo 설치 상태" "⚠️" "이 모듈에서는 선택 사항"
  fi
else
  record_result 5 "marimo 설치 상태" "⚠️" "uv 미설치 (이 모듈에서 marimo는 선택 사항)"
fi

# --- Check 6: GitHub Secrets ---
if check_command_available gh; then
  secrets_out=$(gh secret list 2>&1 || true)
  if echo "$secrets_out" | grep -q "could not determine"; then
    record_result 6 "GitHub Secrets" "❌" "gh CLI 인증 필요 — gh auth login"
  else
    required_secrets=("GCP_SA_KEY" "GCP_PROJECT_ID" "CLAUDE_TOKEN" "GITHUB_PAT")
    missing=()
    for s in "${required_secrets[@]}"; do
      if ! echo "$secrets_out" | grep -q "$s"; then
        missing+=("$s")
      fi
    done
    if [ ${#missing[@]} -eq 0 ]; then
      record_result 6 "GitHub Secrets" "✅" "필수 시크릿 4개 등록 확인"
    else
      record_result 6 "GitHub Secrets" "❌" "누락: ${missing[*]}"
    fi
  fi
else
  record_result 6 "GitHub Secrets" "❌" "gh CLI 미설치 — https://cli.github.com/ 설치"
fi

# --- Check 7: BigQuery data ---
if [ -f .env ]; then
  source_env() { set -a; source .env 2>/dev/null; set +a; }
  source_env
fi
if [ -n "${GCP_PROJECT_ID:-}" ] && [ -n "${BQ_DATASET_RAW:-}" ]; then
  if check_command_available bq; then
    bq_out=$(bq query --nouse_legacy_sql --format=json \
      "SELECT
         (SELECT COUNT(*) FROM \`${GCP_PROJECT_ID}.${BQ_DATASET_RAW}.raw_events\`) AS event_count,
         (SELECT COUNT(*) FROM \`${GCP_PROJECT_ID}.${BQ_DATASET_RAW}.raw_users\`) AS user_count" 2>&1 || true)
    event_count=$(echo "$bq_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['event_count'])" 2>/dev/null || echo "0")
    user_count=$(echo "$bq_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['user_count'])" 2>/dev/null || echo "0")
    if [ "$event_count" -ge 500000 ] 2>/dev/null && [ "$user_count" -ge 10000 ] 2>/dev/null; then
      record_result 7 "BigQuery 데이터" "✅" "events: ${event_count}건, users: ${user_count}건"
    else
      record_result 7 "BigQuery 데이터" "❌" "events: ${event_count}건, users: ${user_count}건 — 합성 데이터 생성 필요"
    fi
  else
    record_result 7 "BigQuery 데이터" "❌" "bq CLI 미설치"
  fi
else
  record_result 7 "BigQuery 데이터" "❌" "GCP_PROJECT_ID 또는 BQ_DATASET_RAW 환경 변수 미설정"
fi

# --- Check 8: dbt models (functional: actually runs dbt run + dbt test) ---
if check_command_available uv && [ -f dbt_project.yml ]; then
  # Functional test: run full dbt pipeline and check exit codes
  dbt_run_exit=0
  dbt_run_out=$(uv run dbt run 2>&1) || dbt_run_exit=$?
  if [ "$dbt_run_exit" -eq 0 ]; then
    dbt_test_exit=0
    dbt_test_out=$(uv run dbt test 2>&1) || dbt_test_exit=$?
    if [ "$dbt_test_exit" -eq 0 ]; then
      record_result 8 "dbt 모델 빌드/테스트" "✅" "dbt run + test 성공"
    else
      fail_count=$(echo "$dbt_test_out" | grep -oE "FAIL=[0-9]+" | head -1 || echo "FAIL=?")
      record_result 8 "dbt 모델 빌드/테스트" "⚠️" "dbt run 성공, 테스트 일부 실패 ($fail_count)"
    fi
  else
    # Diagnose why dbt run failed
    model_files=$(find models -name "*.sql" 2>/dev/null | head -1)
    if [ -z "$model_files" ]; then
      record_result 8 "dbt 모델 빌드/테스트" "❌" "models/ 아래 SQL 파일 없음 — dbt 모델 작성 필요"
    elif [ ! -f profiles.yml ] && [ ! -d "$HOME/.dbt" ]; then
      record_result 8 "dbt 모델 빌드/테스트" "❌" "profiles.yml 없음 — BigQuery 연결 프로필 생성 필요"
    else
      err_line=$(echo "$dbt_run_out" | grep -i "error" | head -1 || echo "상세 내용은 로그 참조")
      record_result 8 "dbt 모델 빌드/테스트" "❌" "dbt run 실패 — ${err_line}"
    fi
  fi
elif [ ! -f dbt_project.yml ]; then
  record_result 8 "dbt 모델 빌드/테스트" "❌" "dbt_project.yml 없음 — 학습자가 프로젝트 초기화 필요"
else
  record_result 8 "dbt 모델 빌드/테스트" "❌" "uv 미설치"
fi

# --- Print results ---
print_results
