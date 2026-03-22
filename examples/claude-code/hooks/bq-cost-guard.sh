#!/usr/bin/env bash
# bq-cost-guard.sh — BigQuery 쿼리 비용 가드
# PreToolUse 훅에서 실행: bq query 실행 전 dry-run으로 스캔 바이트 확인
#
# 사용법: bash .claude/hooks/bq-cost-guard.sh "$TOOL_INPUT"
#
# 비용 한도: 1GB (기본값) — 초과 시 실행 차단
# 환경 변수 BQ_COST_LIMIT_BYTES로 한도 조정 가능

set -euo pipefail

# 비용 한도 (바이트 단위, 기본값 1GB)
COST_LIMIT_BYTES="${BQ_COST_LIMIT_BYTES:-1073741824}"

# 입력에서 쿼리 추출
TOOL_INPUT="$1"

# bq query 명령어가 아니면 통과
if [[ "$TOOL_INPUT" != *"bq query"* ]]; then
    exit 0
fi

# 쿼리 추출 (-- 이후의 SQL 부분)
QUERY=$(echo "$TOOL_INPUT" | sed 's/.*bq query[^"]*"//' | sed 's/"$//')

if [[ -z "$QUERY" ]]; then
    echo "⚠️ 쿼리를 추출할 수 없습니다. 수동으로 확인하세요."
    exit 0
fi

# dry-run 실행으로 스캔 바이트 확인
echo "🔍 BigQuery dry-run 실행 중..."
DRY_RUN_RESULT=$(bq query \
    --dry_run \
    --use_legacy_sql=false \
    --format=json \
    "$QUERY" 2>&1) || {
    echo "❌ dry-run 실패: $DRY_RUN_RESULT"
    exit 1
}

# 스캔 바이트 추출
BYTES=$(echo "$DRY_RUN_RESULT" | grep -oP '"totalBytesProcessed":\s*"\K[0-9]+' || echo "0")

# 사람이 읽기 쉬운 형식으로 변환
if [[ "$BYTES" -gt 1073741824 ]]; then
    HUMAN_SIZE="$(echo "scale=2; $BYTES / 1073741824" | bc) GB"
elif [[ "$BYTES" -gt 1048576 ]]; then
    HUMAN_SIZE="$(echo "scale=2; $BYTES / 1048576" | bc) MB"
else
    HUMAN_SIZE="$(echo "scale=2; $BYTES / 1024" | bc) KB"
fi

echo "📊 예상 스캔량: $HUMAN_SIZE ($BYTES bytes)"

# 한도 초과 확인
if [[ "$BYTES" -gt "$COST_LIMIT_BYTES" ]]; then
    LIMIT_HUMAN="$(echo "scale=2; $COST_LIMIT_BYTES / 1073741824" | bc) GB"
    echo "❌ 비용 한도 초과! (한도: $LIMIT_HUMAN, 예상: $HUMAN_SIZE)"
    echo "   쿼리를 최적화하거나 BQ_COST_LIMIT_BYTES 환경 변수를 조정하세요."
    exit 1
fi

echo "✅ 비용 한도 이내 — 쿼리 실행을 허용합니다."
exit 0
