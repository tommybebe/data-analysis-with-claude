#!/usr/bin/env bash
# setup_data.sh — BigQuery data setup for FitTrack DAU/MAU analysis
#
# Starter script for Module 0. Learners extend this as they build
# the full data pipeline (generate_synthetic_data.py, load_to_bigquery.py).
#
# This script provides two data loading paths:
#   1. dbt seed: Load small sample data from seeds/ (no BigQuery required)
#   2. BigQuery: Generate full synthetic data and load to BigQuery
#
# Usage:
#   bash scripts/setup_data.sh           # Show help
#   bash scripts/setup_data.sh --seed    # dbt seed only (no BigQuery required)
#
# Environment variables:
#   GCP_PROJECT_ID                  Google Cloud project ID (required for BigQuery)
#   GOOGLE_APPLICATION_CREDENTIALS  Path to service account JSON key (required for BigQuery)
#   BQ_DATASET_RAW                  Raw dataset name (default: raw)

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
    echo -e "${BLUE}  FitTrack 데이터 설정 — 모듈 0${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
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
    echo "  --seed      dbt seed 실행 (BigQuery 불필요, seeds/ 디렉토리의 샘플 데이터 사용)"
    echo "  --help      이 도움말 표시"
    echo ""
    echo "전체 BigQuery 데이터 파이프라인 구축:"
    echo "  1. scripts/generate_synthetic_data.py 작성 (합성 데이터 생성)"
    echo "  2. scripts/load_to_bigquery.py 작성 (BigQuery 적재)"
    echo "  3. 이 스크립트에 전체 파이프라인 통합"
    echo ""
    echo "빠른 시작 (dbt seed):"
    echo "  bash scripts/setup_data.sh --seed"
    echo "  → seeds/raw_users.csv (20행)과 seeds/raw_events.csv (80행)을"
    echo "    dbt를 통해 데이터 웨어하우스에 적재합니다."
}

run_dbt_seed() {
    print_step "dbt seed 실행 중 (소규모 샘플 데이터)..."
    if command -v dbt &> /dev/null; then
        dbt seed --profiles-dir . --target dev
        print_success "dbt seed 완료 — seeds/ 디렉토리의 CSV 데이터가 로드되었습니다"
        echo ""
        echo "다음 단계:"
        echo "  1. dbt run     # 모델 실행 (모델을 먼저 작성하세요)"
        echo "  2. dbt test    # 테스트 실행"
    else
        print_error "dbt가 설치되어 있지 않습니다. 'uv sync'를 먼저 실행하세요."
        exit 1
    fi
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
    *)
        show_help
        ;;
esac
