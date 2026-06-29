#!/usr/bin/env bash
# bq-cost-guard.sh — BigQuery query cost guard
# Frozen snapshot from Module 1 output (prerequisite for Module 2)
# Hook type: PreToolUse | Matcher: Bash
# Role: Block queries exceeding scan byte threshold via dry-run estimation

set -euo pipefail

# Read hook input from STDIN
INPUT=$(cat)

# Extract the command from tool_input
COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")

# Only check bq query commands
if [[ "$COMMAND" != *"bq query"* ]]; then
    exit 0
fi

# Skip if already a dry-run
if [[ "$COMMAND" == *"--dry_run"* ]]; then
    exit 0
fi

# Cost threshold from environment variable (default: 1GB)
COST_LIMIT_BYTES="${BQ_COST_LIMIT_BYTES:-1073741824}"

# Extract the SQL query from the command
SQL=$(echo "$COMMAND" | sed -n 's/.*bq query[^"]*"\(.*\)".*/\1/p')
if [[ -z "$SQL" ]]; then
    echo "⚠️ [bq-cost-guard] bq query 명령에서 SQL을 추출할 수 없습니다" >&2
    exit 1
fi

# Run dry-run to estimate scan bytes
DRY_RUN_OUTPUT=$(bq query --dry_run --use_legacy_sql=false "$SQL" 2>&1) || {
    echo "❌ [bq-cost-guard] dry-run 실패: $DRY_RUN_OUTPUT" >&2
    exit 1
}

# Extract bytes from dry-run output
SCAN_BYTES=$(echo "$DRY_RUN_OUTPUT" | grep -oP '\d+' | head -1 || echo "0")

if [[ "$SCAN_BYTES" -gt "$COST_LIMIT_BYTES" ]]; then
    SCAN_MB=$((SCAN_BYTES / 1048576))
    LIMIT_MB=$((COST_LIMIT_BYTES / 1048576))
    echo "❌ [bq-cost-guard] 쿼리 스캔 예상: ${SCAN_MB}MB — 한도 초과 (${LIMIT_MB}MB)" >&2
    echo "   비용 추정: \$$(echo "scale=4; $SCAN_BYTES / 1099511627776 * 5" | bc)  (on-demand \$5/TB)" >&2
    exit 1
fi

SCAN_MB=$((SCAN_BYTES / 1048576))
echo "✅ [bq-cost-guard] 쿼리 스캔 예상: ${SCAN_MB}MB — 한도 이내" >&2
exit 0
