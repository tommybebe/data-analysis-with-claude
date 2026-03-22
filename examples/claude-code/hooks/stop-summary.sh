#!/usr/bin/env bash
# stop-summary.sh — 분석 완료 후 요약 생성
# Stop 훅에서 실행: Claude가 작업을 마칠 때 생성된 산출물을 요약하여 보고
#
# 확인 항목:
# 1. 새로 생성되거나 수정된 파일 목록
# 2. dbt 테스트 결과 (있는 경우)
# 3. 생성된 marimo 노트북
# 4. 리포트 파일

set -euo pipefail

SUMMARY_SEPARATOR="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "$SUMMARY_SEPARATOR"
echo "📋 작업 완료 요약"
echo "$SUMMARY_SEPARATOR"

# 1. Git 상태로 변경된 파일 확인
CHANGED_FILES=$(git status --short 2>/dev/null || echo "")

if [[ -n "$CHANGED_FILES" ]]; then
    echo ""
    echo "📝 변경된 파일:"
    echo "$CHANGED_FILES" | while IFS= read -r line; do
        STATUS="${line:0:2}"
        FILEPATH="${line:3}"
        case "$STATUS" in
            " M"|"M "|"MM") ICON="✏️ " ;;
            "A "|"??")      ICON="➕ " ;;
            " D"|"D ")      ICON="🗑️ " ;;
            *)              ICON="📄 " ;;
        esac
        echo "   ${ICON}${FILEPATH}"
    done
fi

# 2. dbt 테스트 결과 확인 (target/run_results.json이 있는 경우)
DBT_RESULTS_FILE="target/run_results.json"
if [[ -f "$DBT_RESULTS_FILE" ]]; then
    echo ""
    echo "🧪 dbt 테스트 결과:"
    # jq가 있으면 파싱, 없으면 파일 존재 여부만 보고
    if command -v jq &>/dev/null; then
        PASS=$(jq '[.results[] | select(.status == "pass")] | length' "$DBT_RESULTS_FILE" 2>/dev/null || echo "?")
        FAIL=$(jq '[.results[] | select(.status == "fail")] | length' "$DBT_RESULTS_FILE" 2>/dev/null || echo "?")
        WARN=$(jq '[.results[] | select(.status == "warn")] | length' "$DBT_RESULTS_FILE" 2>/dev/null || echo "?")
        echo "   ✅ 통과: ${PASS}  ❌ 실패: ${FAIL}  ⚠️ 경고: ${WARN}"
    else
        echo "   결과 파일: $DBT_RESULTS_FILE (jq 설치 시 상세 확인 가능)"
    fi
fi

# 3. 생성된 marimo 노트북 확인
NOTEBOOKS=$(find notebooks/ -name "*.py" -newer .git/index 2>/dev/null || echo "")
if [[ -n "$NOTEBOOKS" ]]; then
    echo ""
    echo "📓 생성/수정된 marimo 노트북:"
    echo "$NOTEBOOKS" | while IFS= read -r nb; do
        SIZE=$(wc -l < "$nb" 2>/dev/null || echo "?")
        echo "   📄 $nb (${SIZE}줄)"
    done
fi

# 4. 생성된 리포트 파일 확인
if [[ -d "reports/" ]]; then
    REPORTS=$(find reports/ -name "*.html" -o -name "*.pdf" 2>/dev/null | head -5)
    if [[ -n "$REPORTS" ]]; then
        echo ""
        echo "📊 생성된 리포트:"
        echo "$REPORTS" | while IFS= read -r rpt; do
            SIZE_KB=$(du -k "$rpt" 2>/dev/null | cut -f1 || echo "?")
            echo "   📄 $rpt (${SIZE_KB} KB)"
        done
    fi
fi

# 5. 완료 증거 파일 확인
if [[ -d "evidence/" ]]; then
    EVIDENCE=$(find evidence/ -name "*.json" 2>/dev/null | head -5)
    if [[ -n "$EVIDENCE" ]]; then
        echo ""
        echo "🔍 완료 증거:"
        echo "$EVIDENCE" | while IFS= read -r ev; do
            echo "   ✅ $ev"
        done
    fi
fi

echo ""
echo "$SUMMARY_SEPARATOR"
echo ""
