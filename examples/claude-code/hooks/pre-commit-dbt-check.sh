#!/usr/bin/env bash
# pre-commit-dbt-check.sh — 커밋 전 dbt 검증
# PreCommit 훅에서 실행: dbt 모델 변경이 포함된 커밋 시 자동 검증
#
# 검증 항목:
# 1. 변경된 dbt 모델이 정상 빌드되는지
# 2. 모든 데이터 테스트가 통과하는지
# 3. 소스 freshness가 정상인지

set -euo pipefail

# 스테이징된 파일 중 dbt 모델 변경 확인
STAGED_MODELS=$(git diff --cached --name-only -- 'models/**/*.sql' 'models/**/*.yml' 2>/dev/null || echo "")

if [[ -z "$STAGED_MODELS" ]]; then
    echo "ℹ️ dbt 모델 변경 없음 — 검증 건너뜀"
    exit 0
fi

echo "🔍 커밋 전 dbt 검증 시작..."
echo "   변경된 파일:"
echo "$STAGED_MODELS" | sed 's/^/   - /'

# 1단계: 모델 빌드
echo ""
echo "📦 1/3: dbt run 실행..."
if ! dbt run 2>&1 | tail -5; then
    echo "❌ dbt run 실패 — 커밋을 차단합니다."
    echo "   모델 빌드 에러를 수정한 후 다시 커밋하세요."
    exit 1
fi

# 2단계: 테스트 실행
echo ""
echo "🧪 2/3: dbt test 실행..."
TEST_OUTPUT=$(dbt test 2>&1)
TEST_EXIT=$?

if [[ $TEST_EXIT -ne 0 ]]; then
    echo "❌ dbt test 실패 — 커밋을 차단합니다."
    echo "$TEST_OUTPUT" | grep -E "(FAIL|ERROR)" | head -10
    echo ""
    echo "   데이터 테스트를 수정한 후 다시 커밋하세요."
    exit 1
fi

PASS_COUNT=$(echo "$TEST_OUTPUT" | grep -c "PASS" || echo "0")
echo "   ✅ ${PASS_COUNT}개 테스트 통과"

# 3단계: 소스 freshness (경고만)
echo ""
echo "🕐 3/3: 소스 freshness 확인..."
FRESHNESS_OUTPUT=$(dbt source freshness 2>&1) || {
    echo "   ⚠️ 소스 freshness 확인 실패 (경고 — 커밋은 허용)"
}

echo ""
echo "✅ dbt 검증 완료 — 커밋을 허용합니다."
exit 0
