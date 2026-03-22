#!/usr/bin/env bash
# dbt-auto-test.sh — dbt 모델 수정 후 자동 테스트
# PostToolUse 훅에서 실행: dbt 모델 파일 수정 시 자동으로 테스트 실행
#
# 수정된 모델과 해당 모델에 의존하는 다운스트림 모델까지 테스트

set -euo pipefail

echo "🧪 dbt 테스트 실행 중..."

# 수정된 파일에서 모델명 추출 (확장자 제거)
# PostToolUse 환경에서 TOOL_INPUT으로 수정된 파일 경로 전달
MODIFIED_FILE="${TOOL_INPUT:-}"
if [[ -n "$MODIFIED_FILE" ]]; then
    MODEL_NAME=$(basename "$MODIFIED_FILE" .sql)
    echo "   대상 모델: $MODEL_NAME (+ 다운스트림)"

    # 수정된 모델 + 다운스트림 모델 테스트
    TEST_OUTPUT=$(dbt test --select "$MODEL_NAME"+ 2>&1) || {
        echo "❌ dbt 테스트 실패:"
        echo "$TEST_OUTPUT" | tail -20
        echo ""
        echo "⚠️ 테스트 실패한 모델을 수정한 후 다시 시도하세요."
        # PostToolUse 훅은 경고만 표시 (차단하지 않음)
        exit 0
    }
else
    # 파일 경로를 알 수 없으면 전체 테스트
    TEST_OUTPUT=$(dbt test 2>&1) || {
        echo "❌ dbt 테스트 실패:"
        echo "$TEST_OUTPUT" | tail -20
        exit 0
    }
fi

# 결과 요약
PASS_COUNT=$(echo "$TEST_OUTPUT" | grep -c "PASS" || echo "0")
FAIL_COUNT=$(echo "$TEST_OUTPUT" | grep -c "FAIL" || echo "0")
WARN_COUNT=$(echo "$TEST_OUTPUT" | grep -c "WARN" || echo "0")

echo "✅ dbt 테스트 완료: ${PASS_COUNT} 통과 / ${FAIL_COUNT} 실패 / ${WARN_COUNT} 경고"
