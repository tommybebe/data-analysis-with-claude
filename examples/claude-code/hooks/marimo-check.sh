#!/usr/bin/env bash
# marimo-check.sh — marimo 노트북 유효성 검사
# PostToolUse 훅에서 실행: .py 파일 수정 후 marimo 노트북 형식 검증
#
# 이벤트: PostToolUse (Write/Edit 도구 실행 후)
# 역할: notebooks/ 디렉토리의 .py 파일 수정 감지 → marimo 앱 형식 검증
#
# 검증 항목:
#   1. import marimo 선언 존재 여부
#   2. app = marimo.App() 패턴 존재 여부
#   3. @app.cell 데코레이터 최소 1개 이상
#   4. Python 문법 오류 여부 (py_compile)
#
# 주의: 이 훅은 경고만 표시하며 작업을 차단하지 않습니다 (exit 0).

set -uo pipefail

# PostToolUse 훅 입력: STDIN으로 JSON 전달됨
HOOK_INPUT=$(cat)

# 수정된 파일 경로 추출
MODIFIED_FILE=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
file_path = data.get('tool_input', {}).get('file_path', '')
print(file_path)
" 2>/dev/null || echo "")

# .py 파일이 아니면 종료
if [[ -z "$MODIFIED_FILE" ]] || [[ "$MODIFIED_FILE" != *.py ]]; then
    exit 0
fi

# notebooks/ 디렉토리 하위의 파일인지 확인
if [[ "$MODIFIED_FILE" != *"notebooks/"* ]]; then
    exit 0
fi

echo "" >&2
echo "📓 [marimo-check] $(basename "$MODIFIED_FILE") 노트북 유효성 검사 시작..." >&2

# 파일 존재 확인
if [[ ! -f "$MODIFIED_FILE" ]]; then
    echo "   ⚠️  파일을 찾을 수 없습니다: $MODIFIED_FILE" >&2
    exit 0
fi

ERRORS=0

# 1. Python 문법 검사
echo "   1️⃣  Python 문법 검사..." >&2
if ! python3 -m py_compile "$MODIFIED_FILE" 2>/dev/null; then
    SYNTAX_ERROR=$(python3 -m py_compile "$MODIFIED_FILE" 2>&1)
    echo "   ❌ Python 문법 오류:" >&2
    echo "      $SYNTAX_ERROR" >&2
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ Python 문법 정상" >&2
fi

# 2. marimo import 확인
if ! grep -q "import marimo" "$MODIFIED_FILE" 2>/dev/null; then
    echo "   ❌ 'import marimo' 선언이 없습니다." >&2
    echo "      marimo 노트북은 반드시 'import marimo as mo'로 시작해야 합니다." >&2
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ marimo import 확인됨" >&2
fi

# 3. app = marimo.App() 패턴 확인
if ! grep -qE "app\s*=\s*marimo\.App\(" "$MODIFIED_FILE" 2>/dev/null; then
    echo "   ⚠️  'app = marimo.App()' 패턴이 없습니다." >&2
    echo "      marimo 앱 초기화가 필요합니다." >&2
    # 경고만, 에러로 처리하지 않음 (일부 템플릿 허용)
else
    echo "   ✅ marimo.App() 초기화 확인됨" >&2
fi

# 4. @app.cell 데코레이터 확인
CELL_COUNT=$(grep -c "@app\.cell" "$MODIFIED_FILE" 2>/dev/null || echo "0")
if [[ "$CELL_COUNT" -eq 0 ]]; then
    echo "   ⚠️  @app.cell 데코레이터가 없습니다." >&2
    echo "      분석 노트북에는 최소 1개 이상의 셀이 필요합니다." >&2
else
    echo "   ✅ 셀 수: ${CELL_COUNT}개" >&2
fi

# 5. 한국어 주석/레이블 확인 (권고)
KO_COUNT=$(grep -c "#.*[가-힣]" "$MODIFIED_FILE" 2>/dev/null || echo "0")
if [[ "$KO_COUNT" -gt 0 ]]; then
    echo "   ✅ 한국어 주석 ${KO_COUNT}개 확인됨" >&2
fi

# 결과 출력
echo "" >&2
if [[ "$ERRORS" -gt 0 ]]; then
    echo "   ⚠️  [marimo-check] ${ERRORS}개 문제 발견 — 노트북을 수정하세요." >&2
else
    echo "   ✅ [marimo-check] 유효성 검사 통과" >&2
fi
echo "" >&2

exit 0
