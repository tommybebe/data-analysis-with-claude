#!/usr/bin/env bash
# stop-summary.sh — Session end summary generation
# Frozen snapshot from Module 1 output (prerequisite for Module 2)
# Hook type: Stop
# Role: Improve observability — log session activity to evidence/session_log.json

set -euo pipefail

mkdir -p evidence

# Collect session metadata
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S%z')
MODIFIED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -20 || echo "")
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null | head -20 || echo "")

# Count changes
MODIFIED_COUNT=$(echo "$MODIFIED_FILES" | grep -c '.' 2>/dev/null || echo "0")
STAGED_COUNT=$(echo "$STAGED_FILES" | grep -c '.' 2>/dev/null || echo "0")

# Generate JSON log
python3 -c "
import json, sys

log = {
    'session_end': '$TIMESTAMP',
    'modified_files_count': int('$MODIFIED_COUNT'),
    'staged_files_count': int('$STAGED_COUNT'),
    'modified_files': [f for f in '''$MODIFIED_FILES'''.strip().split('\n') if f],
    'staged_files': [f for f in '''$STAGED_FILES'''.strip().split('\n') if f],
}

with open('evidence/session_log.json', 'w') as f:
    json.dump(log, f, indent=2, ensure_ascii=False)

print(json.dumps(log, indent=2, ensure_ascii=False), file=sys.stderr)
"

echo "=== 세션 완료 요약 ===" >&2
echo "종료 시각: $TIMESTAMP" >&2
echo "수정 파일: ${MODIFIED_COUNT}개, 스테이지 파일: ${STAGED_COUNT}개" >&2
echo "상세 로그: evidence/session_log.json" >&2
exit 0
