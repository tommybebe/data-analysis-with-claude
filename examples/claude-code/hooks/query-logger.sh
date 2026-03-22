#!/usr/bin/env bash
# query-logger.sh — BigQuery 쿼리 실행 로그 기록
# PostToolUse 훅에서 실행: bq query 명령 실행 후 비용 기록
#
# 이벤트: PostToolUse (Bash 도구 실행 후)
# 역할: bq query 명령 감지 → 스캔 바이트 및 비용을 JSONL 로그에 기록
#
# 로그 파일: .claude/logs/query-log.jsonl
# 형식: 한 줄에 하나의 JSON 객체 (JSONL 포맷)

set -uo pipefail

LOG_FILE=".claude/logs/query-log.jsonl"
mkdir -p "$(dirname "$LOG_FILE")"

# PostToolUse 훅 입력: STDIN으로 JSON 전달됨
HOOK_INPUT=$(cat)

# 도구 정보 및 입력/출력 추출
TOOL_NAME=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_name', ''))
" 2>/dev/null || echo "")

# Bash 도구가 아니면 종료
if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

TOOL_COMMAND=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")

# bq query 명령이 아니면 종료
if [[ "$TOOL_COMMAND" != *"bq query"* ]]; then
    exit 0
fi

# dry-run이면 스킵 (비용 없음)
if [[ "$TOOL_COMMAND" == *"--dry_run"* ]]; then
    exit 0
fi

# 도구 출력에서 스캔 바이트 추출
TOOL_OUTPUT=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_response', {}).get('output', ''))
" 2>/dev/null || echo "")

# BigQuery 출력에서 처리된 바이트 수 추출
BYTES_PROCESSED=$(echo "$TOOL_OUTPUT" | python3 -c "
import sys, re, json
output = sys.stdin.read()

# 패턴 1: JSON 출력
try:
    data = json.loads(output)
    stats = data.get('statistics', {})
    print(stats.get('totalBytesProcessed', '0'))
    sys.exit(0)
except:
    pass

# 패턴 2: 텍스트 출력에서 regex
patterns = [
    r'Bytes processed:\s*([0-9,]+)',
    r'totalBytesProcessed[\":\s]+([0-9]+)',
    r'([0-9.]+)\s*(?:GB|MB|KB)\s+processed',
]
for pattern in patterns:
    match = re.search(pattern, output, re.IGNORECASE)
    if match:
        # 쉼표 제거 후 숫자 반환
        val = match.group(1).replace(',', '')
        print(val)
        sys.exit(0)

print('0')
" 2>/dev/null || echo "0")

BYTES_PROCESSED=${BYTES_PROCESSED:-0}

# 쿼리 텍스트 추출 (로깅용, 짧게 잘라서 저장)
QUERY_SNIPPET=$(echo "$TOOL_COMMAND" | \
    sed "s/.*bq query[^'\"]*['\"]//;s/['\"].*//;s/\s\+/ /g" | \
    cut -c1-200)

# 예상 비용 계산 ($5/TB)
COST_USD=$(python3 -c "print(f'{$BYTES_PROCESSED / 1099511627776 * 5:.6f}')" 2>/dev/null || echo "0")

# JSONL 로그에 기록
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ENTRY=$(python3 -c "
import json
entry = {
    'timestamp': '$TIMESTAMP',
    'command': 'bq_query',
    'bytes_processed': $BYTES_PROCESSED,
    'cost_usd': $COST_USD,
    'query_snippet': '''$QUERY_SNIPPET'''.strip()[:200]
}
print(json.dumps(entry, ensure_ascii=False))
" 2>/dev/null || echo "{\"timestamp\":\"$TIMESTAMP\",\"bytes_processed\":$BYTES_PROCESSED}")

echo "$LOG_ENTRY" >> "$LOG_FILE"

# 임계값 초과 시 경고 출력
WARNING_THRESHOLD_BYTES=5368709120  # 5GB
if [[ "$BYTES_PROCESSED" -gt "$WARNING_THRESHOLD_BYTES" ]]; then
    BYTES_GB=$(python3 -c "print(f'{$BYTES_PROCESSED / 1073741824:.2f}')" 2>/dev/null || echo "?")
    echo "" >&2
    echo "⚠️  [query-logger] 대용량 쿼리 실행됨: ${BYTES_GB} GB" >&2
    echo "   비용: \$${COST_USD} USD | 로그: $LOG_FILE" >&2
fi

exit 0
