#!/usr/bin/env bash
# setup_data.sh — BigQuery data setup for FitTrack DAU/MAU analysis
#
# This script orchestrates the full data pipeline:
#   1. Generate synthetic user and event data (CSV)
#   2. Load CSV data into BigQuery raw dataset
#   3. Optionally run dbt seed for local testing
#
# Prerequisites:
#   - Python dependencies installed: uv sync
#   - GCP authentication configured
#   - Environment variables set (see .env.example)
#
# Usage:
#   bash scripts/setup_data.sh           # Full setup (generate + load to BigQuery)
#   bash scripts/setup_data.sh --seed    # dbt seed only (no BigQuery required)
#   bash scripts/setup_data.sh --help    # Show this help message
#
# Environment variables:
#   GCP_PROJECT_ID                  Google Cloud project ID (required for BigQuery)
#   GOOGLE_APPLICATION_CREDENTIALS  Path to service account JSON key (required for BigQuery)
#   BQ_DATASET_RAW                  Raw dataset name (default: raw)
#   DATASET_LOCATION                Dataset location (default: US)
#   SYNTHETIC_NUM_USERS             Number of users to generate (default: 10000)
#   SYNTHETIC_START_DATE            Event data start date (default: 2026-01-01)
#   SYNTHETIC_END_DATE              Event data end date (default: 2026-03-31)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  FitTrack 데이터 설정${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

show_help() {
    echo "사용법: bash scripts/setup_data.sh [옵션]"
    echo ""
    echo "옵션:"
    echo "  (없음)      합성 데이터 생성 후 BigQuery에 적재"
    echo "  --seed      dbt seed만 실행 (BigQuery 불필요, 소규모 샘플 데이터)"
    echo "  --generate  합성 데이터 CSV만 생성 (BigQuery 적재 안 함)"
    echo "  --help      이 도움말 표시"
    echo ""
    echo "환경 변수:"
    echo "  GCP_PROJECT_ID                  GCP 프로젝트 ID (BigQuery 사용 시 필수)"
    echo "  GOOGLE_APPLICATION_CREDENTIALS  서비스 계정 JSON 키 경로 (BigQuery 사용 시 필수)"
    echo "  BQ_DATASET_RAW                  Raw 데이터셋 이름 (기본값: raw)"
    echo "  SYNTHETIC_NUM_USERS             생성할 사용자 수 (기본값: 10000)"
    echo "  SYNTHETIC_START_DATE            이벤트 시작 일자 (기본값: 2026-01-01)"
    echo "  SYNTHETIC_END_DATE              이벤트 종료 일자 (기본값: 2026-03-31)"
}

run_dbt_seed() {
    print_step "dbt seed 실행 중 (소규모 샘플 데이터)..."
    if command -v dbt &> /dev/null; then
        dbt seed --profiles-dir . --target dev
        print_success "dbt seed 완료 — seeds/ 디렉토리의 CSV 데이터가 로드되었습니다"
    else
        print_error "dbt가 설치되어 있지 않습니다. 'uv sync'를 먼저 실행하세요."
        exit 1
    fi
}

run_generate() {
    print_step "합성 데이터 생성 중..."
    echo "  사용자 수: ${SYNTHETIC_NUM_USERS:-10000}"
    echo "  기간: ${SYNTHETIC_START_DATE:-2026-01-01} ~ ${SYNTHETIC_END_DATE:-2026-03-31}"
    echo ""

    if command -v uv &> /dev/null; then
        uv run python scripts/generate_synthetic_data.py
    else
        python scripts/generate_synthetic_data.py
    fi

    print_success "데이터 생성 완료 — data/raw_users.csv, data/raw_events.csv"
}

run_load() {
    # Validate required env vars for BigQuery
    if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
        print_error "GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다."
        echo "  .env.example을 참고하여 .env 파일을 생성하세요."
        exit 1
    fi

    if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
        print_error "GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되지 않았습니다."
        echo "  GCP 서비스 계정 JSON 키 경로를 설정하세요."
        exit 1
    fi

    if [[ ! -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
        print_error "서비스 계정 키 파일을 찾을 수 없습니다: ${GOOGLE_APPLICATION_CREDENTIALS}"
        exit 1
    fi

    print_step "BigQuery에 데이터 적재 중..."
    echo "  프로젝트: ${GCP_PROJECT_ID}"
    echo "  데이터셋: ${BQ_DATASET_RAW:-raw}"
    echo ""

    if command -v uv &> /dev/null; then
        uv run python scripts/load_to_bigquery.py
    else
        python scripts/load_to_bigquery.py
    fi

    print_success "BigQuery 적재 완료"
}

# Main
print_header

case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --seed)
        run_dbt_seed
        ;;
    --generate)
        run_generate
        ;;
    *)
        # Full setup: generate + load
        run_generate
        echo ""
        run_load
        echo ""
        print_success "전체 데이터 설정 완료!"
        echo ""
        echo "다음 단계:"
        echo "  1. dbt deps                    # dbt 패키지 설치"
        echo "  2. dbt run                     # 모델 실행"
        echo "  3. dbt test                    # 테스트 실행"
        ;;
esac
