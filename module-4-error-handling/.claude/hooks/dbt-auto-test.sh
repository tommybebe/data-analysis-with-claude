#!/usr/bin/env bash
# dbt-auto-test.sh — Auto-compile dbt models after SQL file changes
# Frozen snapshot from Module 1 output (prerequisite for Module 4)
# Hook type: PostToolUse | Matcher: Write, Edit
# Role: Automatically verify dbt model syntax after SQL file modifications

set -euo pipefail

# Read hook input from STDIN
INPUT=$(cat)

# Extract the file path from tool_input
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('tool_input', {}).get('file_path', ''))" 2>/dev/null || echo "")

# Only check SQL files in models/ directory
if [[ "$FILE_PATH" != models/*.sql && "$FILE_PATH" != models/**/*.sql ]]; then
    exit 0
fi

# Run dbt compile to verify syntax
echo "🔄 [dbt-auto-test] dbt compile 실행 중..." >&2
COMPILE_OUTPUT=$(uv run dbt compile 2>&1) || {
    echo "❌ [dbt-auto-test] dbt compile 실패:" >&2
    echo "$COMPILE_OUTPUT" >&2
    exit 1
}

echo "✅ [dbt-auto-test] dbt compile 성공" >&2
exit 0
