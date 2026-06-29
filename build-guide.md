# 빌드 가이드 — 하니스 참조 구현

> **하니스 엔지니어링 for 데이터 분석** 코스의 모듈 1~4 단계별 실습 및 참조 구현(reference implementation)

이 문서는 각 모듈에서 구축하는 하니스 컴포넌트의 **전체 소스와 빌드 단계**를 담습니다. 훅 스크립트, `settings.json`, 슬래시 커맨드 본문, 권한 정책, GitHub Actions 워크플로의 완성 형태와 작성 과정을 한곳에서 보여줍니다.

## 문서의 위치

| 문서 | 역할 |
|------|------|
| [`course-spec.md`](course-spec.md) | 코스 명세 — 학습 목표·핵심 개념·자기 점검 기준 (WHAT / WHY) |
| **`build-guide.md`** (이 문서) | 빌드 가이드 — 단계별 실습과 참조 구현 소스 (HOW) |
| `module-N-*/README.md` | 학습자용 단계별 활동 가이드 |
| `module-N-*/.claude/`, `models/`, `.github/` | **실제 동작하는 산출 파일 (source of truth)** |

> ⚠️ **단일 출처 원칙**: 이 문서의 코드 블록은 각 모듈 디렉터리의 **정본 파일을 그대로 옮긴 참조 사본**입니다. 로직과 주석 언어가 실제 파일과 일치하며(구조 주석은 영문, 사용자 출력 메시지·본문은 한국어 — 정본 파일의 스타일 그대로), 모듈별 `# Frozen snapshot from Module N output …` 출처 표기 줄만 생략했습니다. 실제로 실행되는 정본 파일은 각 모듈 디렉터리(`module-N-*/.claude/hooks/`, `.claude/commands/`, `.claude/settings.json`, `.github/workflows/`, `.claude/prompts/` 등)에 있으며, 동작 검증·수정은 항상 모듈 디렉터리의 파일을 기준으로 하세요. `/hello` 커맨드, `settings.json` 점진적 스니펫, permissions 발췌처럼 정본 파일이 없거나 일부만 보여 주는 교육용 예시는 그 취지를 본문에 명시했습니다.

---

## 모듈 0: 환경 설정

모듈 0의 환경·인프라 설정(레포 클론, GCP 서비스 계정, GitHub Secret, 합성 데이터 생성·적재, dbt 빌드)은 [`instructor-setup-guide.md`](instructor-setup-guide.md)와 [`module-0-project-setup/README.md`](module-0-project-setup/README.md)에서 단계별로 다룹니다.

---

## 모듈 1: 훅과 설정 엔지니어링 — settings.json으로 에이전트 정책 구현
#### 사전 준비

모듈 1을 시작하기 전에 `AGENTS.md`가 존재해야 합니다. 모듈 0에서 생성하지 않았다면 먼저 작성하거나, 아래 최소 AGENTS.md로 시작할 수 있습니다:

```bash
# 최소 AGENTS.md 빠른 생성 (모듈 0 완료 후 이미 있다면 건너뜀)
cat > AGENTS.md << 'EOF'
# FitTrack 데이터 분석 에이전트 가이드

## BigQuery 정책
- 분석용 데이터셋: `fittrack_analytics` (읽기/쓰기 허용)
- 단일 쿼리 스캔 한도: 1GB 이하 (초과 시 dry-run 확인 후 진행)
- 프로덕션 데이터셋: `fittrack_production` (읽기 전용)

## dbt 모델 규약
- 분석 쿼리는 `models/marts/` 레이어(fct_*, dim_*)를 기반으로 작성
- 새 모델에는 `unique` + `not_null` 테스트 필수

## 금지 사항
- `git push --force` — 이력 손상 위험
- `bq rm`, `DROP TABLE`, `DELETE FROM` — 데이터 손실
- 스캔 1GB 초과 쿼리의 dry-run 없는 실행
EOF
```

### 활동

**활동 1: settings.json 구조 탐색 및 첫 번째 훅 등록** *(예상 소요: 15~20분)*

> 🔧 **하니스 설정**: `.claude/settings.json`과 그 안에 등록하는 훅 스크립트는 순수한 **하니스 설정**입니다. 에이전트가 실행하는 dbt 모델이나 BigQuery 쿼리 결과는 파이프라인 산출물이지만, 훅은 그 실행을 제어하는 정책 레이어입니다.

```bash
# .claude 디렉토리와 하위 구조 생성
mkdir -p .claude/hooks

# settings.json 스켈레톤 생성
cat > .claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {}
}
EOF

# JSON 문법 검증 (오류 없으면 포맷된 JSON 출력)
cat .claude/settings.json | python -m json.tool
```

가장 간단한 훅부터 등록합니다 — `Stop` 이벤트에 `echo` 명령을 실행하는 테스트 훅:

```bash
# Stop 훅 테스트 스크립트
cat > .claude/hooks/stop-summary.sh << 'EOF'
#!/usr/bin/env bash
# stop-summary.sh — 세션 종료 시 작업 요약 출력
# 역할: 하니스의 가시성(observability) 향상 — 에이전트가 무엇을 했는지 기록

# 현재 시각과 마지막 수정 파일 목록 출력
echo "=== 세션 완료 요약 ===" >&2
echo "종료 시각: $(date '+%Y-%m-%d %H:%M:%S')" >&2
echo "최근 수정 파일:" >&2
git diff --name-only HEAD 2>/dev/null | head -10 >&2 || echo "  (git 변경 없음)" >&2
exit 0
EOF
chmod +x .claude/hooks/stop-summary.sh
```

`settings.json`에 Stop 훅 등록:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/stop-summary.sh" }
        ]
      }
    ]
  }
}
```

동작 확인:
```bash
# Claude Code 세션 시작 후 간단한 작업 후 종료 — Stop 훅 실행 확인
claude "현재 날짜를 알려줘"
# 종료 시 "=== 세션 완료 요약 ===" 메시지 출력 확인
```

**활동 2: PreToolUse 훅 — BigQuery 비용 가드 구현** *(예상 소요: 25~30분)*

> 💰 **비용 의식**: BigQuery on-demand 가격은 $5/TB입니다. 1GB 쿼리는 약 $0.005(0.5센트)로 소액이지만, 잘못 작성된 쿼리가 50GB를 스캔하면 $0.25가 됩니다. 에이전트가 반복적으로 실행할 수 있으므로 훅으로 자동 차단이 필수입니다.

`.claude/hooks/bq-cost-guard.sh` 생성:

```bash
cat > .claude/hooks/bq-cost-guard.sh << 'HOOKEOF'
#!/usr/bin/env bash
# bq-cost-guard.sh — BigQuery query cost guard
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
HOOKEOF
chmod +x .claude/hooks/bq-cost-guard.sh
```

`settings.json`에 PreToolUse 훅 추가:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/stop-summary.sh" }
        ]
      }
    ]
  }
}
```

**훅 차단 동작 테스트** (성공 경로뿐만 아니라 차단 경로도 반드시 검증):

```bash
# 환경변수로 임계값을 1바이트로 낮춰 차단 동작 강제 테스트
# 실제 BigQuery 쿼리 없이도 차단 메시지가 출력되는지 확인
export BQ_COST_LIMIT_BYTES=1

echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' \
  | bash .claude/hooks/bq-cost-guard.sh

# 기대 출력: BigQuery 연결 시 "❌ [bq-cost-guard] 쿼리 스캔 예상: NMB — 한도 초과 (0MB)",
#           연결이 없으면 "❌ [bq-cost-guard] dry-run 실패: ..." — 두 경우 모두 exit 1
echo "훅 종료 코드: $?"  # 1이어야 함

# 테스트 후 원래 값 복원
unset BQ_COST_LIMIT_BYTES
```

> **BigQuery 실제 연결 없이 테스트**: dry-run 실행이 실패하면 훅이 exit 1을 반환합니다. 이 자체가 차단 동작의 검증입니다 (BigQuery 연결이 없으면 dry-run 실패 → 훅 차단).

**활동 3: PostToolUse 훅 — dbt 자동 컴파일 검증** *(예상 소요: 20~25분)*

dbt SQL 파일이 편집될 때마다 자동으로 `dbt compile`을 실행하여 SQL 문법 오류를 즉시 감지합니다:

```bash
cat > .claude/hooks/dbt-auto-test.sh << 'HOOKEOF'
#!/usr/bin/env bash
# dbt-auto-test.sh — Auto-compile dbt models after SQL file changes
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
HOOKEOF
chmod +x .claude/hooks/dbt-auto-test.sh
```

`settings.json`에 PostToolUse 훅 추가:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }] }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }]
      },
      {
        "matcher": "Edit",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }]
      }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "bash .claude/hooks/stop-summary.sh" }] }
    ]
  }
}
```

**의도적 실패 테스트**:

```bash
# 문법 오류가 있는 임시 dbt 모델 생성
echo "SELEC * FORM broken_table" > models/marts/test_broken.sql

# 에이전트가 이 파일을 편집했다고 가정하고 훅 직접 실행
echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/test_broken.sql"}}' \
  | bash .claude/hooks/dbt-auto-test.sh

# 기대 결과: "❌ [dbt-auto-test] dbt compile 실패" 메시지

# 테스트 파일 정리
rm models/marts/test_broken.sql
```

**활동 4: permissions.allow / permissions.deny 정책 설정** *(예상 소요: 15~20분)*

`permissions.allow`와 `permissions.deny`는 훅보다 먼저 평가되는 **정적 ACL(접근 제어 목록)**입니다. 훅은 동적 검증이지만, permissions는 패턴 매칭으로 즉시 허용/거부합니다.

```bash
# settings.json에 permissions 섹션 추가 (전체 파일)
cat > .claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(dbt debug:*)",
      "Bash(dbt deps:*)",
      "Bash(dbt ls:*)",
      "Bash(dbt source freshness:*)",
      "Bash(bq query --dry_run:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout:*)",
      "Bash(git push:*)",
      "Bash(gh issue:*)",
      "Bash(gh pr:*)",
      "Bash(python3:*)",
      "Bash(jq:*)",
      "Read",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(bq rm:*)",
      "Bash(dbt run --full-refresh:*)",
      "Bash(rm -rf:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/bq-cost-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/dbt-auto-test.sh"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/dbt-auto-test.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/stop-summary.sh"
          }
        ]
      }
    ]
  }
}
EOF

# JSON 문법 최종 검증
python -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 정상"
```

**permissions 규칙 해설**:

| 규칙 패턴 | 의미 | 분류 이유 |
|-----------|------|---------|
| `Bash(dbt run:*)` | `dbt run` 뒤 어떤 인수도 허용 | allow — dbt 실행은 분석의 핵심 |
| `Bash(bq query --dry_run:*)` | dry_run 플래그가 있는 bq query만 허용 | allow — dry-run은 안전 |
| `Bash(git push --force:*)` | force push 차단 | deny — 이력 손상 위험 |
| `Bash(bq rm:*)` | BigQuery 리소스 삭제 차단 | deny — 데이터 손실 |
| `Bash(dbt run --full-refresh:*)` | 전체 새로고침 차단 | deny — 대량 스캔 비용 위험 |

> **설계 원칙**: `deny`는 최소한으로 유지하고, 구체적인 패턴을 사용합니다. 너무 넓은 deny(`Bash(*)`)는 에이전트를 무력화합니다. 너무 좁은 allow(`Bash(dbt run --select fct_*:*)`)는 정당한 작업을 막습니다.

**활동 5: Stop 훅 — 작업 완료 요약 생성** *(예상 소요: 15~20분)*

Stop 훅을 업그레이드하여 분석 세션의 작업 요약을 `evidence/` 디렉토리에 저장합니다:

```bash
cat > .claude/hooks/stop-summary.sh << 'HOOKEOF'
#!/usr/bin/env bash
# stop-summary.sh — Session end summary generation
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
HOOKEOF
chmod +x .claude/hooks/stop-summary.sh
```

**활동 6: 훅 의도적 실패 테스트 및 디버깅** *(예상 소요: 15~20분)*

훅이 정상 동작하는지 확인하는 것만큼 **의도적으로 실패시키고 디버깅하는 것**이 중요합니다. 이것이 훅 엔지니어링의 핵심 역량입니다:

```bash
# 1. JSON 문법 오류 주입 테스트 — 오류가 있는 settings.json
echo '{"hooks": {"PreToolUse": [' > /tmp/bad_settings.json
python -m json.tool /tmp/bad_settings.json 2>&1 | head -3
# 기대: "Expecting value" 같은 JSON 파싱 오류 → settings.json은 항상 검증 후 저장

# 2. 훅 스크립트 실행 권한 누락 테스트
chmod -x .claude/hooks/bq-cost-guard.sh
# Claude Code 세션에서 bq query 실행 시 훅이 실행되지 않는 것 확인 (permission denied)
# 복구:
chmod +x .claude/hooks/bq-cost-guard.sh

# 3. 매처 너무 좁게 설정 시 → 정상 명령이 훅을 우회하는 것 확인
# "Bash(bq query --use_legacy_sql=false *)" 패턴은
# "bq query --nouse_legacy_sql ..." 명령은 감지하지 못함
# 교훈: 매처 패턴은 실제 에이전트가 생성하는 명령 형식에 맞게 테스트 필요

# 4. 전체 설정 최종 검증
echo "=== settings.json 검증 ===" && python -m json.tool .claude/settings.json && echo "✅ JSON 정상"
echo "=== 훅 스크립트 권한 확인 ===" && ls -la .claude/hooks/*.sh
```

#### Claude Code 프롬프트 예제

**settings.json 초안 생성**:

```bash
claude "AGENTS.md의 BigQuery 정책과 dbt 규약을 읽고
.claude/settings.json을 생성해줘.
permissions.allow: dbt run/test/compile/source freshness/ls/deps/debug,
bq query --dry_run, git status/log/diff/add/commit/checkout/push,
gh issue view/list, gh pr create/list, python3, jq, Read, Write, Edit
permissions.deny: git push --force, bq rm, dbt run --full-refresh, rm -rf
hooks:
- PreToolUse/Bash: bash .claude/hooks/bq-cost-guard.sh (비용 가드)
- PostToolUse/Write: bash .claude/hooks/dbt-auto-test.sh (dbt 컴파일 검증)
- PostToolUse/Edit: bash .claude/hooks/dbt-auto-test.sh
- Stop: bash .claude/hooks/stop-summary.sh (세션 요약)
생성 후 python -m json.tool로 JSON 문법 검증해줘."
```

**훅 스크립트 일괄 생성**:

```bash
claude "AGENTS.md의 BigQuery 비용 정책(1GB 한도, $5/TB)을 읽고
다음 3개 훅 스크립트를 생성해줘:
1. .claude/hooks/bq-cost-guard.sh
   - PreToolUse, Bash 매처
   - bq query 명령 감지 → dry-run 비용 확인 → BQ_COST_LIMIT_BYTES(기본 1GB) 초과 시 exit 1
   - 예상 스캔량, 비용, 판정 메시지 stderr 출력
2. .claude/hooks/dbt-auto-test.sh
   - PostToolUse, Write/Edit 매처
   - models/**/*.sql 파일 변경 시 dbt compile 실행 → 실패 시 exit 1
3. .claude/hooks/stop-summary.sh
   - Stop 이벤트
   - git diff --name-only로 변경 파일 목록 → evidence/session_log.json 저장
각 스크립트 생성 후 chmod +x 실행, JSON 주석(# 설명)으로 훅 타입과 역할 명시."
```

#### 관찰-수정-창작 사이클

**관찰(observe)**

훅 설정 전후로 동일한 에이전트 작업을 실행하여 차이를 관찰합니다:

```bash
# 훅 없는 상태 (훅 등록 전 또는 임시 비활성화 상태)에서 실행:
# 에이전트가 비용이 큰 쿼리를 실행하면 아무 경고 없이 진행됨

# 훅 등록 후 실행:
# - bq query 실행 시 비용 가드 훅 작동
# - dbt SQL 파일 편집 시 자동 컴파일 검증
# - 세션 종료 시 작업 요약 생성
```

**회고 질문**

아래 질문에 대한 답변을 `evidence/module-1-retrospective.md`에 기록하세요.

**영역 A: 훅 동작 검증**

1. **비용 가드 차단 테스트 결과**: `BQ_COST_LIMIT_BYTES=1`로 설정하여 강제 차단을 테스트했을 때 어떤 메시지가 출력되었는가? 실제 BigQuery 연결 없이도 차단 동작을 검증하는 방법은 무엇인가?

2. **의도적 실패 케이스**: 훅 스크립트를 의도적으로 실패시키는 방법을 3가지 나열하라 (예: 실행 권한 제거, JSON 문법 오류, 훅 경로 오탈자). 각각을 어떻게 디버깅하는가?

**영역 B: 정책 설계 판단**

3. **매처 범위 트레이드오프**: `PreToolUse` 훅의 매처를 `"Bash"` (모든 Bash)로 설정했을 때 vs `"Bash(bq query*)"` (bq query만)로 설정했을 때, 각각의 false positive와 false negative는 어떤 것이 있는가?

4. **permissions vs hooks 선택 기준**: `git push --force`를 차단할 때 `permissions.deny`를 사용하는 것이 더 나은가, 아니면 `PreToolUse` 훅으로 구현하는 것이 더 나은가? 두 접근법의 차이점을 설명하라.

**영역 C: 하니스 정합성**

5. **AGENTS.md와 settings.json 정합성**: `AGENTS.md`에 "BigQuery 스캔 1GB 한도"를 명시했다면, `bq-cost-guard.sh`의 `BQ_COST_LIMIT_BYTES` 기본값도 `1073741824` (1GB)이어야 합니다. 이 수치가 일치하는지 확인하고, 단일 소스(예: `.claude/thresholds.env`)에서 관리하는 구조를 설계하라.

**하니스 생성**

회고 결과를 바탕으로:

1. **매처 패턴 조정**: false positive가 발생한 훅의 매처 패턴을 좁혀 수정합니다
2. **임계값 환경 파일 생성**: `.claude/thresholds.env`에 `BQ_COST_LIMIT_BYTES=1073741824` 정의 후 훅 스크립트에서 `source .claude/thresholds.env`로 로드하는 구조로 리팩토링
3. **JSON 스키마 검증 자동화**: `python -m json.tool .claude/settings.json`을 pre-commit 훅에 포함하여 settings.json 수정 시 JSON 문법 자동 검증

---

## 모듈 2: 슬래시 커맨드 작성 — 에이전트 작업 명세화
#### 사전 준비

모듈 2는 모듈 1(훅과 설정 엔지니어링)을 완료한 후 시작합니다. 다음이 준비되어 있어야 합니다:

```
✅ .claude/settings.json   — 훅 등록 완료 (모듈 1 산출물)
✅ .claude/hooks/          — bq-cost-guard.sh, dbt-auto-test.sh, stop-summary.sh
✅ AGENTS.md               — BigQuery 정책, dbt 규약 포함
✅ analyses/, evidence/, reports/ 디렉토리 존재
```

`.claude/commands/` 디렉토리는 **아직 없는 상태**입니다 — 이것이 모듈 2의 핵심 산출물입니다.

### 활동

**활동 1: .claude/commands/ 구조 파악 및 첫 번째 커맨드 작성** *(예상 소요: 15~20분)*

> 🔧 **하니스 설정**: `.claude/commands/` 디렉토리의 모든 `.md` 파일은 **하니스 설정**입니다. 에이전트가 이 커맨드를 사용하여 생성하는 marimo 노트북, dbt 모델, JSON 증거는 **파이프라인 산출물**입니다.

```bash
# .claude/commands 디렉토리 생성
mkdir -p .claude/commands

# 가장 단순한 커맨드부터 시작 — /hello
cat > .claude/commands/hello.md << 'EOF'
# /hello — 커맨드 구조 연습

이 커맨드는 커맨드 파일 구조를 이해하기 위한 예제입니다. (정본 파일이 아닌 교육용 예시 — 실제 커맨드와 동일한 섹션 구조를 따릅니다)

## Input
- `$ARGUMENTS`: 인사 대상 이름 (예: `/hello FitTrack팀`)

## Execution Steps
1. 현재 시각과 `$ARGUMENTS`에 입력된 이름을 포함한 인사말을 출력
2. `AGENTS.md`를 읽고 프로젝트명과 주요 구성 요소(BigQuery, dbt, marimo)를 한 줄로 요약

## Output
```
안녕하세요, [이름]! [현재 시각]
프로젝트: FitTrack 데이터 분석 — BigQuery + dbt + marimo 기반
```

## Constraints
- 외부 API 호출 금지
- 파일 생성/수정 없이 읽기 작업만 수행
EOF

# 테스트
claude "/hello 데이터팀"
```

> **관찰 포인트**: `/hello 데이터팀` 실행 시 `$ARGUMENTS`가 "데이터팀"으로 대체되어 출력되는지 확인합니다. 커맨드 파일이 에이전트의 프롬프트 역할을 하는 것을 직접 체험하는 것이 이 활동의 목적입니다.

**활동 2: /analyze 커맨드 — 분석 요청 → 노트북 생성 전 과정 명세화** *(예상 소요: 25~30분)*

> 💰 **BigQuery 비용 내장**: `/analyze` 커맨드는 쿼리 실행 전 dry-run 비용 확인 단계를 반드시 포함합니다. 새 쿼리 추가 시 예상 비용을 미리 출력하는 것이 on-demand 가격 환경에서의 필수 습관입니다. 합성 데이터(~100MB) 기준 DAU 쿼리 1회 실행 약 $0.0003.

```bash
cat > .claude/commands/analyze.md << 'EOF'
# /analyze — 분석 요청 파싱부터 marimo 노트북 생성까지

분석 요청을 파싱하여 dbt 모델을 탐색하고, 비용을 확인한 후, marimo 노트북을 생성합니다.

## Input
- `$ARGUMENTS`: 분석 요청 텍스트 (예: "2026년 1월 DAU", "1분기 플랫폼별 MAU 추이")

## Execution Steps
1. `$ARGUMENTS`에서 분석 대상 기간, 지표, 세분화 기준을 파싱
2. 사용 가능한 dbt 모델 탐색: `dbt ls --resource-type model`
3. 분석에 필요한 mart 모델 식별 (fct_daily_active_users, fct_monthly_active_users, fct_retention_cohort)
4. BigQuery dry-run으로 비용 사전 확인: `bq query --dry_run --use_legacy_sql=false "SELECT ..."`
5. 비용이 BQ_COST_LIMIT_BYTES 이내인 경우에만 진행
6. marimo 노트북 생성: `analyses/analysis_[metric]_[YYYYMM].py`
7. 노트북에 BigQuery 쿼리, 시각화, 인사이트 요약 포함
8. evidence/analysis_manifest.json에 분석 메타데이터 기록

## Output
- `analyses/analysis_[metric]_[YYYYMM].py` — marimo 노트북 파일
- `evidence/analysis_manifest.json` — 분석 실행 메타데이터

## Constraints
- 반드시 dbt mart 모델을 통해 데이터 접근 (raw 테이블 직접 접근 금지)
- BigQuery dry-run 비용 확인 후 진행
- 노트북 파일명은 analysis_[metric]_[YYYYMM].py 형식 준수
- 환경 변수 사용 (GCP_PROJECT_ID, BQ_DATASET_ANALYTICS 등 하드코딩 금지)
EOF
```

테스트:

```bash
# 커맨드 실행 — 실제 BigQuery 연결이 있으면 분석 수행, 없으면 커맨드 구조 확인
claude "/analyze 2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"

# 노트북 파일 생성 확인
ls analyses/*.py
```

**활동 3: /check-cost 커맨드 작성** *(예상 소요: 15~20분)*

`/check-cost`는 분석 작업 시작 전 BigQuery 쿼리 비용을 빠르게 확인하는 유틸리티 커맨드입니다:

```bash
cat > .claude/commands/check-cost.md << 'EOF'
# /check-cost — BigQuery 쿼리 비용 사전 추정

BigQuery dry-run을 사용하여 쿼리 실행 전 비용을 추정합니다.

## Input
- `$ARGUMENTS`: SQL 쿼리 또는 자연어 설명 (예: "SELECT count(*) FROM analytics.fct_daily_active_users")

## Execution Steps
1. `$ARGUMENTS`가 SQL이면 직접 사용, 자연어면 적절한 SQL 생성
2. dry-run 실행: `bq query --dry_run --use_legacy_sql=false "$SQL"`
3. 스캔 바이트 추출 및 비용 계산 ($5/TB on-demand)
4. 안전성 판단:
   - ✅ Safe: < 500MB
   - ⚠️ Warning: 500MB ~ 1GB
   - ❌ Dangerous: > 1GB
5. evidence/query_cost_log.json에 결과 기록

## Output
```
=== BigQuery 비용 추정 ===
쿼리: [SQL]
스캔 예상: [N] MB ([N] bytes)
비용 추정: $[N] (on-demand $5/TB)
판정: [✅ Safe / ⚠️ Warning / ❌ Dangerous]
```

- `evidence/query_cost_log.json` — 비용 추정 로그

## Constraints
- 실제 쿼리를 실행하지 않음 (dry-run만 실행)
- 환경 변수 사용 (프로젝트 ID, 데이터셋명 하드코딩 금지)
- BQ_COST_LIMIT_BYTES 환경 변수 참조
EOF
```

테스트:

```bash
# 간단한 쿼리로 비용 확인 테스트
claude "/check-cost SELECT COUNT(*) FROM \`<project>.fittrack_analytics.fct_daily_active_users\`"
# 기대 출력: 예상 스캔량, 비용, ✅/⚠️/❌ 판정
```

**활동 4: /validate-models 및 /generate-report 커맨드 작성** *(예상 소요: 20~25분)*

```bash
# /validate-models — dbt 모델 빌드 및 테스트 실행
cat > .claude/commands/validate-models.md << 'EOF'
# /validate-models — dbt 모델 검증 및 테스트 결과 기록

dbt 테스트를 실행하여 모델 품질을 검증하고 결과를 JSON으로 저장합니다.

## Input
- `$ARGUMENTS`: 검증 대상 모델 (선택사항, 예: "staging", "marts", 또는 특정 모델명)

## Execution Steps
1. `$ARGUMENTS`로 대상 범위 결정 (없으면 전체 모델)
2. dbt 테스트 실행: `dbt test` 또는 `dbt test --select $ARGUMENTS`
3. 테스트 결과 파싱 (통과/실패/경고/에러 수)
4. evidence/dbt_test_results.json에 결과 기록

## Output
- `evidence/dbt_test_results.json` — 테스트 결과 JSON

```json
{
  "timestamp": "2026-01-15T10:30:00+09:00",
  "total_tests": 15,
  "passed": 14,
  "failed": 1,
  "warnings": 0,
  "errors": 0,
  "failed_tests": ["test_name_here"],
  "target_selection": "$ARGUMENTS or 'all'"
}
```

## Constraints
- dbt test 실행 전 dbt compile로 문법 검증
- JSON에 total_tests, passed, failed 필드 필수 포함
- 실패한 테스트의 구체적 이름 기록
EOF

# /generate-report — marimo 노트북 → HTML/PDF 내보내기
cat > .claude/commands/generate-report.md << 'EOF'
# /generate-report — marimo 노트북 보고서 내보내기

marimo 노트북을 HTML 보고서로 내보내고 매니페스트를 기록합니다.

## Input
- `$ARGUMENTS`: 대상 노트북 경로 또는 패턴 (예: "analyses/analysis_dau_202601.py")

## Execution Steps
1. `$ARGUMENTS`로 대상 노트북 식별 (없으면 analyses/ 디렉터리 전체)
2. 각 노트북에 대해 marimo export 실행: `marimo export html [notebook.py] -o [output.html]`
3. 생성된 파일 목록 수집
4. evidence/report_manifest.json에 매니페스트 기록

## Output
- 생성된 HTML 보고서 파일
- `evidence/report_manifest.json` — 보고서 매니페스트

```json
{
  "timestamp": "2026-01-15T10:30:00+09:00",
  "outputs": [
    {
      "source": "analyses/analysis_dau_202601.py",
      "format": "html",
      "path": "analyses/analysis_dau_202601.html",
      "size_bytes": 45678
    }
  ],
  "total_reports": 1
}
```

## Constraints
- marimo export 사용 (marimo run이 아님)
- JSON에 outputs[].format, outputs[].path 필드 필수 포함
- 노트북이 존재하지 않으면 에러 메시지와 함께 중단
EOF
```

**활동 5: $ARGUMENTS 변수 활용 — 동적 커맨드 설계** *(예상 소요: 10~15분)*

`$ARGUMENTS`를 더 구조화된 방식으로 파싱하도록 커맨드를 개선합니다:

```bash
# analyze.md에 구조화된 입력 파싱 추가
# 다음 형식을 지원:
# /analyze 지표: DAU 기간: 2026-01~2026-03 세그먼트: platform
# /analyze #42
# /analyze 2026년 Q1 DAU 추이

# 테스트: 동일한 커맨드로 다른 기간 분석
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31"
# → analyses/analysis_dau_202601.py 생성 확인

claude "/analyze 2026년 2월 DAU 기간: 2026-02-01~2026-02-28"
# → analyses/analysis_dau_202602.py 생성 확인 (202601과 다른 파일)

ls analyses/
# 기대 출력: analysis_dau_202601.py, analysis_dau_202602.py
```

> **$ARGUMENTS 활용 원칙**:
> - 구조화 입력(`키: 값` 형식)이 자유 형식 텍스트보다 에이전트의 파싱 일관성이 높습니다
> - 커맨드 파일의 `## Input` 섹션에서 예시 형식을 명확하게 제시하면 에이전트가 정확하게 파싱합니다
> - `$ARGUMENTS`가 비어있을 경우의 기본값 동작을 `## Constraints`에 명시하세요

**활동 6: 커맨드 체인 실습 및 완료 증거 설계** *(예상 소요: 15~20분)*

슬래시 커맨드를 순서대로 실행하는 분석 체인을 수행합니다:

```bash
# 전체 분석 체인 — 순서가 중요
# 1. 비용 확인 (선택적 but 권장)
claude "/check-cost SELECT date, COUNT(DISTINCT user_id) as dau FROM \`<project>.fittrack_analytics.fct_daily_active_users\` WHERE date BETWEEN '2026-01-01' AND '2026-01-31' GROUP BY 1 ORDER BY 1"

# 2. 분석 실행
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31 세그먼트: platform"

# 3. dbt 모델 검증
claude "/validate-models"

# 4. 리포트 생성
claude "/generate-report analyses/analysis_dau_202601.py"

# 5. 최종 산출물 확인
tree analyses/ evidence/ reports/
cat evidence/dbt_test_results.json | python -m json.tool
```

> **커맨드 체인 설계 원칙**: 각 커맨드는 독립적으로 실행 가능해야 합니다. `/generate-report`가 `/analyze` 결과에 의존한다면 `## 사전 조건` 섹션에 명시하여 에이전트가 순서를 인지하게 합니다.

#### Claude Code 프롬프트 예제

**커맨드 파일 일괄 생성**:

```bash
claude "AGENTS.md를 읽고 FitTrack 프로젝트용 4개 슬래시 커맨드를 생성해줘.
.claude/commands/ 아래에 analyze.md, validate-models.md, generate-report.md, check-cost.md를 생성해줘.
각 파일에 ## 입력, ## 실행 단계, ## 출력, ## 제약 조건 섹션 포함.
analyze.md: 분석 요청 파싱 → 기존 mart 모델 탐색 → 비용 dry-run 확인 → 신규 dbt 모델(필요 시) → marimo 노트북(analyses/ 경로) → 완료 증거 JSON 저장(evidence/).
check-cost.md: $ARGUMENTS SQL dry-run → 스캔량·비용·판정(✅안전 / ⚠️주의 / ❌위험).
validate-models.md: dbt run → dbt test → evidence/dbt_test_results.json 저장.
generate-report.md: marimo export html → reports/ 저장 → evidence/report_manifest.json 저장.
BigQuery on-demand 비용 기준: $5/TB. 한도: 1GB."
```

**커맨드 프롬프트 개선 요청**:

```bash
claude "/analyze를 실행해보니 파일명이 analyses/analysis_202601.py로 생성됐어.
AGENTS.md의 marimo 규약에 따르면 파일명은 analysis_[지표]_[기간].py 형식이어야 해.
analyze.md의 실행 단계 5단계에서 파일명 생성 로직을 더 구체적으로 명시해줘:
지표는 $ARGUMENTS에서 추출한 주제(영문, 소문자, 언더스코어)를 사용하고,
기간은 YYYYMM 형식으로 시작일의 연월을 사용해줘."
```

#### 관찰-수정-창작 사이클

**관찰(observe)**

커맨드 작성 전후로 동일한 분석 요청의 결과를 비교합니다:

```bash
# 커맨드 없이 자유 형식 프롬프트
claude "2026년 1월 DAU 추이를 분석하고 marimo 노트북으로 만들어줘"
# 결과: 파일명, 노트북 구조, 증거 파일 생성 여부가 매번 달라질 수 있음

# 커맨드 사용 후
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31 세그먼트: platform"
# 결과: analyze.md에 명세된 단계가 일관되게 실행됨
```

**회고 질문**

아래 질문에 대한 답변을 `evidence/module-2-retrospective.md`에 기록하세요.

**영역 A: 커맨드 명세 품질**

1. **추측 발생 분석**: `/analyze` 커맨드 실행 시 에이전트가 명세하지 않은 사항을 추측한 경우가 있었는가? (예: 파일명 형식, 차트 종류, 데이터 필터링 기준) 추측을 없애려면 커맨드의 어느 섹션에 어떤 내용을 추가해야 하는가?

2. **커맨드 경계 설계**: `/analyze` 커맨드가 너무 많은 책임(비용 확인 + 모델 작성 + 노트북 생성 + 증거 저장)을 가지고 있지는 않은가? 이를 더 작은 커맨드로 분리하면 어떤 장단점이 있는가?

**영역 B: $ARGUMENTS 활용**

3. **파싱 일관성**: `$ARGUMENTS`에 자유 형식 텍스트를 입력했을 때 에이전트가 기간, 세그먼트 등을 항상 올바르게 파싱했는가? 파싱 실패를 줄이기 위해 `## 입력` 섹션에 어떤 예시와 형식을 추가할 수 있는가?

4. **기본값 처리**: `$ARGUMENTS`가 비어있거나 형식이 잘못된 경우 에이전트가 어떻게 행동했는가? 커맨드 파일에 기본값 처리 로직을 명시하면 더 나은 결과를 얻을 수 있는가?

**영역 C: 커맨드-훅 연계**

5. **훅 보완 역할**: 모듈 1에서 설정한 `bq-cost-guard.sh` PreToolUse 훅과 `/check-cost` 커맨드가 비용 관련 작업을 어떻게 나누어 담당하는가? 둘 다 필요한 이유는 무엇인가? (힌트: 사전 명시적 확인 vs 자동 차단)

6. **완료 증거의 충분성**: `evidence/dbt_test_results.json`, `query_cost_log.json`, `report_manifest.json` 3개 파일로 "분석이 올바르게 완료되었다"는 것을 기계적으로 검증할 수 있는가? 검증할 수 없는 항목은 무엇인가? (예: DAU ≤ MAU 검증)

**하니스 생성**

회고 결과를 바탕으로:

1. **커맨드 명세 개선**: 추측이 발생한 단계에 더 구체적인 지시와 예시를 추가합니다
2. **$ARGUMENTS 파싱 강화**: 입력 형식 예시를 `## 입력` 섹션에 최소 2개 추가합니다
3. **완료 증거 확장**: 의미론적 검증(`evidence/metric_sanity_check.json` — `dau <= mau`) 항목을 `/validate-models` 커맨드에 추가합니다
4. **커맨드 README 작성**: `.claude/commands/README.md`에 4개 커맨드의 역할과 실행 순서를 정리합니다

---

## 모듈 3: 권한 오케스트레이션 — Claude Code 권한 정책으로 에이전트 경계 설계
### 활동

**활동 1: Claude Code 권한 모델 구조 탐색 및 설정 파일 계층 이해** *(예상 소요: 15~20분)*

> 🔧 **하니스 vs 산출물**: 권한 설정(`.claude/settings.json`)은 **하니스 설정**입니다. 이것이 에이전트가 생성하는 DAU 분석 차트(산출물)를 만들어내는 것이 아니라, 에이전트가 어떤 방식으로 일할 수 있는지를 결정하는 경계입니다.

현재 레포의 Claude Code 설정 파일 현황을 파악합니다:

```bash
# 전역 설정 파일 확인 (모든 세션에 적용)
cat ~/.claude/settings.json 2>/dev/null || echo "전역 설정 없음"

# 프로젝트 설정 파일 확인 (이 레포에만 적용)
cat .claude/settings.json 2>/dev/null || echo "프로젝트 설정 없음"

# 로컬 개발자 설정 파일 확인 (gitignore 권장)
cat .claude/settings.local.json 2>/dev/null || echo "로컬 설정 없음"

# 현재 settings.json의 permissions 섹션 확인 (모듈 1에서 생성)
python -m json.tool .claude/settings.json | grep -A 20 '"permissions"'
```

**모듈 1에서 설정한 권한 현황 점검**: 이미 `permissions.allow`와 `permissions.deny`가 있다면 어떤 규칙이 있는지 확인합니다. 없다면 이 모듈에서 처음 설계합니다.

**활동 2: 데이터 분석 에이전트를 위한 허용 규칙(allow) 설계 및 구현** *(예상 소요: 20~25분)*

> 💰 **BigQuery 비용 관련 권한**: 정본 `.claude/settings.json`의 `allow`는 비용이 발생하지 않는 `Bash(bq query --dry_run:*)`만 통과시킵니다. 실제 `bq query` 실행은 모듈 1의 PreToolUse 훅(`bq-cost-guard.sh`)이 dry-run으로 비용을 확인한 뒤 통과/차단합니다 — 권한 설정만으로는 비용을 제어할 수 없고, 훅이 실제 비용 가드를 담당합니다.

아래는 정본 `.claude/settings.json`의 `permissions.allow` 전체입니다 (모듈 1에서 만들어 모듈 3에서 검토·확정한 최소 권한 집합):

```json
{
  "permissions": {
    "allow": [
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(dbt debug:*)",
      "Bash(dbt deps:*)",
      "Bash(dbt ls:*)",
      "Bash(dbt source freshness:*)",
      "Bash(bq query --dry_run:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout:*)",
      "Bash(git push:*)",
      "Bash(gh issue:*)",
      "Bash(gh pr:*)",
      "Bash(python3:*)",
      "Bash(jq:*)",
      "Read",
      "Write",
      "Edit"
    ]
  }
}
```

허용 규칙 설계 원칙 (정본 settings.json 기준):
- **비용 없는 작업만 직접 허용**: `bq query --dry_run:*`만 allow에 두고, 비용이 발생하는 실제 `bq query`는 `bq-cost-guard.sh` 훅으로 통제
- **git 작업 분리**: `git push:*`는 허용하되, `git push --force:*`는 deny 목록에서 차단
- **GitHub CLI**: 이슈·PR 관리에 필요한 `gh issue:*`, `gh pr:*`만 허용
- **읽기/쓰기·분석 보조**: `Read`, `Write`, `Edit`와 `python3:*`, `jq:*` 허용

다음 Claude Code 프롬프트로 권한 설계를 에이전트에게 요청합니다:

```bash
claude "현재 .claude/settings.json을 분석하고, FitTrack 데이터 분석 에이전트가
필요한 최소 권한이 permissions.allow에 모두 포함되어 있는지 검토해줘.

필요한 작업 유형:
1. dbt 모델 실행/테스트/컴파일/디버그 (dbt run, dbt test, dbt compile, dbt debug, dbt deps, dbt ls)
2. 비용 없는 BigQuery 비용 확인 (bq query --dry_run)
3. Git 작업 (status, log, diff, add, commit, checkout, push)
4. GitHub CLI로 이슈·PR 관리 (gh issue, gh pr)
5. 분석 보조 (python3, jq) 및 파일 도구 (Read, Write, Edit)

실제 bq query(비용 발생)는 allow에 두지 말고 bq-cost-guard.sh 훅으로 통제하는 이유를 설명하고,
최소 권한 원칙(principle of least privilege)을 적용해줘.

검토 후 python -m json.tool .claude/settings.json으로 문법 검증해줘."
```

**활동 3: 위험 작업 차단을 위한 거부 규칙(deny) 구현 및 동작 검증** *(예상 소요: 20~25분)*

되돌리기 어려운(irreversible) 작업을 차단하는 거부 규칙을 구현하고, 실제로 차단되는지 검증합니다. 아래는 정본 `.claude/settings.json`의 `permissions.deny` 전체입니다 (`deny`는 최소·구체적으로 유지 — 너무 넓은 deny는 에이전트를 무력화):

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(bq rm:*)",
      "Bash(dbt run --full-refresh:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

**거부 규칙 동작 검증**:

```bash
# deny 설정 후 검증 — git push --force 차단 확인
claude "git push --force origin main 명령을 실행해줘"
# 기대 출력: Permission denied 또는 해당 명령이 허용되지 않는다는 메시지

# bq rm 차단 확인
claude "bq rm fittrack_raw.raw_events 테이블을 삭제해줘"
# 기대 출력: 거부 메시지 (테이블을 실제로 삭제하려 하면 안 됨)
```

> **관찰 포인트**: 에이전트가 거부 메시지를 받았을 때 어떻게 반응하는지 관찰하세요. 좋은 에이전트는 "이 명령이 차단되었으므로 대안을 제시합니다"와 같이 응답하고, 나쁜 에이전트는 무한 루프에 빠지거나 우회를 시도합니다. 우회를 시도한다면 deny 규칙을 더 강화해야 합니다.

**활동 4: GitHub Actions `permissions:` 키 설계** *(예상 소요: 15~20분)*

GitHub Actions 워크플로 YAML에서 CI 환경의 권한을 설계합니다:

```yaml
# .github/workflows/auto-analyze.yml 권한 섹션 (정본 발췌 — 전체 워크플로는 모듈 4에서 구현)
name: Auto Analyze Pipeline

on:
  issues:
    types: [labeled]

# 워크플로 실행에 필요한 최소 권한
permissions:
  issues: write        # 이슈 코멘트 작성 + 라벨 부착/제거
  contents: write      # 파일 커밋, 브랜치 생성
  pull-requests: write # PR 생성 + 라벨 부착

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      # ... (상세 단계는 모듈 4에서 구현)
```

**권한 설계 문서 작성** (`evidence/module-3-permissions-rationale.md`):

```markdown
# 권한 설계 근거 (module-3)

## Claude Code permissions.allow/deny — 로컬 개발 환경

### 허용 규칙 (allow) 근거
| 규칙 | 필요한 이유 |
|------|------------|
| `Bash(bq query --dry_run:*)` | 비용 없는 dry-run으로 쿼리 스캔량 사전 확인 |
| `Bash(dbt run:*)` | dbt 모델 빌드 |
| ... | ... |

### 거부 규칙 (deny) 근거
| 규칙 | 차단 이유 |
|------|----------|
| `Bash(git push --force:*)` | 히스토리 파괴 방지 |
| `Bash(bq rm:*)` | 데이터 테이블 실수 삭제 방지 |
| ... | ... |

## GitHub Actions permissions — CI 환경

### 로컬 vs CI 권한 비교
| 항목 | 로컬 (settings.json) | CI (YAML permissions:) |
|------|---------------------|------------------------|
| git push | allow (개발자 리뷰 후 Push) | contents: write (자동 PR 브랜치) |
| 이슈 관리 | 직접 gh CLI 실행 | issues: write |
| 제한 수준 | 중간 (개발자가 즉시 오류 확인 가능) | 엄격 (자동 실행으로 오류 확산 위험) |
```

다음 Claude Code 프롬프트로 권한 문서를 자동 생성합니다:

```bash
claude "현재 .claude/settings.json의 permissions 섹션을 분석하고,
evidence/module-3-permissions-rationale.md 파일을 생성해줘.

포함할 내용:
1. 각 allow 규칙의 필요한 이유 (표 형식)
2. 각 deny 규칙의 차단 이유 (표 형식)
3. 로컬 개발 환경 vs CI 환경 권한 비교 (표 형식)
4. GitHub Actions permissions: 키의 각 항목별 근거

각 근거는 '이 작업이 없으면 X 단계에서 Y가 실패한다'는 형식으로 구체적으로 작성해줘."
```

**활동 5: 로컬 vs CI 다중 환경 권한 정책 설계** *(예상 소요: 15~20분)*

데이터 분석 팀의 실제 운영 환경에서는 동일한 에이전트 코드가 두 가지 맥락에서 실행됩니다:

| 실행 맥락 | 설명 | 권한 설계 방향 |
|-----------|------|---------------|
| **개발자 로컬** | 분석가가 탐색적 분석 또는 하니스 개발 시 Claude Code 대화형 사용 | 더 많은 도구 허용, 빠른 반복 개발 지원 |
| **CI/CD 파이프라인** | GitHub Actions에서 이슈 라벨 트리거로 자동 실행 | 최소 권한, 명시적 단계, 감사 추적 |

**다중 환경 권한 설계 패턴**:

```bash
# 로컬 개발자용 설정 (.claude/settings.json) - 팀 공유
claude "현재 .claude/settings.json의 allow 목록에 개발 편의를 위한 추가 권한을 검토해줘.
예: git log, git diff, git status, python, uv 실행 등 분석 개발에 유용한 명령들.
단, deny 목록은 로컬에서도 동일하게 유지해야 해."

# CI 파이프라인에서는 GitHub Actions permissions: 키로 별도 제어
# 에이전트 코드 자체는 동일하지만, 실행 컨텍스트의 권한이 다름
```

> **설계 원칙**: `deny` 목록은 로컬과 CI 모두에서 동일하게 유지합니다. "로컬에서도 force push는 안 됩니다." `allow` 목록은 CI에서 더 제한적일 수 있습니다 — CI 환경에서 불필요한 탐색적 명령(예: `git log`, `python 스크립트`)이 실행될 필요가 없기 때문입니다.

**활동 6: 권한 경계 종합 테스트 및 회고** *(예상 소요: 10~15분)*

현재까지 구현한 권한 정책 전체를 검증합니다:

```bash
# 전체 권한 정책 검증 체크리스트
echo "=== 권한 정책 검증 ==="

# 1. JSON 문법 검증
python -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 유효" || echo "❌ JSON 문법 오류"

# 2. allow 규칙 수 확인
ALLOW_COUNT=$(python -c "import json; d=json.load(open('.claude/settings.json')); print(len(d.get('permissions',{}).get('allow',[])))")
echo "허용 규칙 수: $ALLOW_COUNT (최소 3개 권장)"

# 3. deny 규칙 수 확인
DENY_COUNT=$(python -c "import json; d=json.load(open('.claude/settings.json')); print(len(d.get('permissions',{}).get('deny',[])))")
echo "거부 규칙 수: $DENY_COUNT (최소 3개 권장)"

# 4. 필수 deny 규칙 존재 여부 확인
python -c "
import json
d = json.load(open('.claude/settings.json'))
deny = d.get('permissions', {}).get('deny', [])
required = ['git push --force', 'bq rm', 'rm -rf']
for r in required:
    found = any(r in rule for rule in deny)
    print(f'{'✅' if found else '❌'} deny에 {r!r} 포함: {found}')
"
```

회고 질문을 `evidence/module-3-permissions-retrospective.md`에 기록합니다:

1. 권한 정책을 설계하는 과정에서 가장 판단하기 어려웠던 부분은 무엇인가? (예: 어떤 명령을 allow에 넣어야 할지 vs deny에 넣어야 할지)
2. 모듈 1에서 이미 기초적인 권한을 설정했는데, 이 모듈에서 추가적으로 설계한 부분은 무엇인가?
3. GitHub Actions의 `permissions:` 키와 Claude Code의 `permissions.allow/deny`가 서로 어떻게 보완적으로 작동하는지 한 문단으로 설명하라.


---

## 모듈 4: 종단간 에이전트 기반 데이터 분석 워크플로 — 하니스 전체 통합 및 실행
### 활동

**활동 1: 하니스 구성 요소 통합 검증** *(예상 소요: 15~20분)*

> 🔧 **이 활동의 목적**: 모듈 4에서 전체 파이프라인을 실행하기 전에, 모듈 1~3에서 구축한 하니스가 모두 올바르게 설정되어 있는지 검증합니다. 이것이 "종단간 파이프라인의 전제 조건 점검"입니다.

```bash
# 모듈 1~3 구성 요소 통합 점검
echo "=== 하니스 구성 요소 통합 점검 ==="

# 모듈 1 확인: 훅 스크립트 존재
echo "[모듈 1] 훅 스크립트..."
ls -la .claude/hooks/bq-cost-guard.sh 2>/dev/null && echo "✅ bq-cost-guard.sh 존재" || echo "❌ bq-cost-guard.sh 없음"

# 모듈 1 확인: settings.json 존재 및 훅 등록
echo "[모듈 1] settings.json 훅 설정..."
python -c "import json; d=json.load(open('.claude/settings.json')); print('✅ hooks 존재' if 'hooks' in d else '❌ hooks 없음')"

# 모듈 2 확인: 슬래시 커맨드 파일 존재
echo "[모듈 2] 슬래시 커맨드..."
ls .claude/commands/*.md 2>/dev/null && echo "✅ 커맨드 파일 존재" || echo "❌ .claude/commands/*.md 없음"

# 모듈 3 확인: 권한 정책 적용
echo "[모듈 3] 권한 정책..."
python -c "
import json
d = json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
allow_count = len(p.get('allow', []))
deny_count = len(p.get('deny', []))
print(f'✅ allow {allow_count}개, deny {deny_count}개' if allow_count >= 3 and deny_count >= 3 else f'❌ allow {allow_count}개, deny {deny_count}개 (각 3개 이상 필요)')
"

# GitHub Secrets 확인
echo "[모듈 0] GitHub Secrets..."
gh secret list | grep -E "GCP_SA_KEY|GCP_PROJECT_ID|CLAUDE_TOKEN" | wc -l | xargs echo "✅ Secrets 등록 수:"
```

**활동 2: GitHub Actions 7단계 오케스트레이션 워크플로 YAML 작성** *(예상 소요: 30~40분)*

> 💰 **BigQuery 비용**: 워크플로 YAML 작성 자체는 비용이 발생하지 않습니다. 실제 비용은 활동 4에서 파이프라인 실행 시 발생합니다 (합성 데이터 ~100MB 기준 전체 파이프라인 예상 비용: $0.01~$0.05).

다음 Claude Code 프롬프트로 워크플로 YAML을 처음부터 작성합니다:

```bash
claude "AGENTS.md와 .claude/settings.json을 읽고,
.github/workflows/auto-analyze.yml 파일을 처음부터 작성해줘.

요구사항:
- 트리거: issues 이벤트, labeled 액션
- 실행 조건: auto-analyze 라벨 또는 stage: 접두어 라벨
- 환경: ubuntu-latest, Python 3.12, uv, dbt-bigquery
- 인증: claude setup-token (CLAUDE_TOKEN), GCP 서비스 계정 (GCP_SA_KEY)
- GitHub Actions permissions: issues: write, contents: write, pull-requests: write
- 7단계 라벨별 분기: stage:1-parse ~ stage:7-report
- 각 단계: Claude Agent SDK로 .claude/prompts/stage-N-*.md 프롬프트 실행
- 각 단계 완료: 이슈 코멘트 작성 (<!-- stage:N-complete --> 앵커 포함) + 라벨 전환
- 오류 시: stage:error 라벨 부착 + 오류 코멘트 작성 (<!-- error-category: ... --> 앵커 포함)
- stage:7-report: HTML/PDF 아티팩트 업로드, auto-analyzed 라벨 포함 PR 생성

작성 후 actionlint로 문법 검증하고, 오류가 있으면 수정해줘."
```

**워크플로 라벨 11개 사전 등록**:

```bash
# 7단계 워크플로 라벨 일괄 생성
gh label create "auto-analyze" --color "0E8A16" --description "자동 분석 워크플로 진입점"
gh label create "stage:1-parse" --color "1D76DB" --description "단계 1: 이슈 파싱"
gh label create "stage:2-define" --color "1D76DB" --description "단계 2: 문제 정의"
gh label create "stage:3-deliverables" --color "1D76DB" --description "단계 3: 산출물 명세"
gh label create "stage:4-spec" --color "1D76DB" --description "단계 4: 스펙 작성"
gh label create "stage:5-extract" --color "5319E7" --description "단계 5: 데이터 추출"
gh label create "stage:6-analyze" --color "5319E7" --description "단계 6: 분석 수행"
gh label create "stage:7-report" --color "5319E7" --description "단계 7: 리포트 생성"
gh label create "done" --color "0E8A16" --description "워크플로 완료"
gh label create "stage:error" --color "D93F0B" --description "단계 실행 오류"
gh label create "needs-retry" --color "FBCA04" --description "재시도 필요"

# 라벨 등록 확인
gh label list | grep -cE "auto-analyze|stage:|^done|needs-retry"
# 기대 출력: 11
```

> **색상 규칙**: 초록(`0E8A16`) = 진입/완료, 파랑(`1D76DB`) = 설계 단계(1-4), 보라(`5319E7`) = 실행 단계(5-7), 빨강(`D93F0B`) = 오류, 노랑(`FBCA04`) = 주의

**활동 3: 에이전트 단계별 프롬프트 파일 7개 설계** *(예상 소요: 25~30분)*

각 파이프라인 단계에서 Claude Agent SDK가 참조하는 프롬프트 파일을 설계합니다:

```bash
# 7단계 프롬프트 파일 일괄 생성
claude "AGENTS.md를 읽고, .claude/prompts/ 디렉토리에
stage-1-parse.md부터 stage-7-report.md까지 7개 파일을 생성해줘.

각 파일의 구조:
## 컨텍스트
- 이전 단계 산출물 위치 (이슈 코멘트의 <!-- stage:N-complete --> 앵커)
- AGENTS.md의 핵심 규약 요약 (인라인)

## 작업 지시
- 구체적 작업 단계 (순서 있는 목록)
- 각 단계의 성공 기준 (기계적으로 검증 가능한 형식)

## 산출물
- 생성할 파일 경로와 형식
- 이슈 코멘트로 기록할 내용 (<!-- stage:N-complete --> 앵커 포함)

## 제약 조건
- BigQuery 비용 제한: 단계 5의 각 쿼리는 1GB 미만 스캔
- AGENTS.md 규약: dbt mart 레이어만 참조, staging 직접 참조 금지
- marimo 규약: 첫 셀에 데이터 소스 선언 필수

생성 후 각 파일의 핵심 내용을 요약해줘."
```

**단계별 프롬프트 설계 원칙**:

| 단계 | 가장 중요한 제약 조건 | 이유 |
|------|-------------------|----|
| 1 (파싱) | 이슈 본문 형식 준수 | 후속 단계가 파싱 결과에 의존 |
| 2 (문제 정의) | 비즈니스 의도 유지 | 잘못된 분석 방향 방지 |
| 3 (산출물 명세) | 구체적 파일 경로와 형식 | 단계 6, 7에서 파일을 찾을 수 있어야 함 |
| 4 (스펙 작성) | BigQuery 쿼리 계획을 dry-run으로 비용 사전 확인 | 단계 5 실행 전 비용 통제 |
| 5 (데이터 추출) | 1GB 비용 제한 + dbt 테스트 통과 확인 | 가장 비용이 큰 단계 |
| 6 (분석 수행) | marimo 노트북 첫 셀 데이터 소스 선언 | 재현 가능성 보장 |
| 7 (리포트 생성) | PR 본문에 evidence/ 파일 링크 포함 | 완료 증거의 추적 가능성 |

**활동 4: 전체 파이프라인 종단간 실행** *(예상 소요: 20~25분)*

> 💰 **BigQuery 비용 추정**: 합성 데이터 기준 7단계 파이프라인 1회 실행 비용은 약 $0.01~$0.05입니다. `evidence/query_cost_log.json`에서 단계별 스캔 바이트를 실시간으로 추적합니다.

```bash
# 1. 분석 요청 이슈 생성 (이슈 본문은 인라인으로 작성)
gh issue create \
  --title "[분석] FitTrack 2026년 1분기 DAU/MAU 트렌드 분석" \
  --body "## 분석 요청

**기간**: 2026-01-01 ~ 2026-03-31
**지표**: DAU, MAU, DAU/MAU 비율
**세분화**: 플랫폼별 (iOS, Android)
**목적**: 1분기 사용자 활동 트렌드 파악 및 리텐션 분석"

# 2. 이슈 번호 확인
ISSUE_NUMBER=$(gh issue list --limit 1 --json number -q '.[0].number')
echo "이슈 번호: #$ISSUE_NUMBER"

# 3. auto-analyze 라벨 부착 — 파이프라인 시작
gh issue edit $ISSUE_NUMBER --add-label "auto-analyze"

# 4. 워크플로 실행 실시간 모니터링
gh run watch

# 5. 이슈 라벨 전환 이력 확인
gh issue view $ISSUE_NUMBER --json labels,timelineItems
```

**관찰 초점**: 라벨이 `auto-analyze` → `stage:1-parse` → ... → `done` 순서로 정확히 전환되는가? 모듈 1에서 구현한 `bq-cost-guard.sh` 훅이 단계 5 실행 시 자동으로 작동하는가? 모듈 3에서 설계한 `permissions.allow/deny`가 에이전트의 행동을 실제로 제한하는가?

**활동 5: 의도적 오류 발생 및 복구 실습** *(예상 소요: 15~20분)*

```bash
# 1. GCP_SA_KEY를 의도적으로 무효화 (INFRA 오류 시뮬레이션)
gh secret set GCP_SA_KEY --body "invalid_key_for_testing"

# 2. stage:5-extract 라벨 부착하여 데이터 추출 단계 트리거
gh issue edit $ISSUE_NUMBER --add-label "stage:5-extract"

# 3. 오류 발생 후 이슈 코멘트 확인
gh issue view $ISSUE_NUMBER --comments | grep -A 5 "error-category"
# 기대 출력: <!-- error-category: INFRA --> 포함 코멘트

# 4. Secret 복구 후 파이프라인 재개
gh secret set GCP_SA_KEY < key.json  # 원래 키 복구

# 5. stage:error 라벨 제거 + stage:5-extract 재부착으로 재개
gh issue edit $ISSUE_NUMBER --remove-label "stage:error"
gh issue edit $ISSUE_NUMBER --add-label "stage:5-extract"
```

> **복구 원칙**: `stage:error` 라벨을 제거하고 실패한 단계의 라벨을 재부착하면, 파이프라인이 해당 단계부터 재개됩니다. 이전 단계를 다시 실행하지 않으므로, 이미 완료된 단계의 산출물이 이슈 코멘트에 남아 있어야 합니다.

**활동 6: 파이프라인 비용 측정, 하니스 효과 회고 및 문서화** *(예상 소요: 20~25분)*

```bash
# BigQuery 비용 측정
python3 -c "
import json

# evidence/query_cost_log.json에서 단계별 비용 집계
with open('evidence/query_cost_log.json') as f:
    log = json.load(f)

total_bytes = sum(entry.get('estimated_bytes', 0) for entry in log)
total_cost_usd = total_bytes / (1024**4) * 5  # on-demand: $5/TB

print(f'총 스캔 데이터: {total_bytes / (1024**3):.2f} GB')
print(f'총 비용 (on-demand): \${total_cost_usd:.4f}')
print(f'비용 정책 (1GB 제한): {\"✅ 준수\" if total_bytes < 1024**3 else \"❌ 초과\"}')
"
```

**관찰-수정-창작 사이클**: 전체 파이프라인 실행을 관찰한 결과를 바탕으로 `evidence/module-4-retrospective.md`를 작성합니다:

```markdown
## 파이프라인 실행 회고 — 영역 A: 하니스 통합 효과

1. 모듈 1~3에서 구축한 하니스 구성 요소(훅, 권한, 슬래시 커맨드) 중
   파이프라인 실행 중 실제로 동작했음을 확인한 것은?
   - 훅 동작 여부: (예: bq-cost-guard.sh가 stage:5에서 실행됨)
   - 권한 거부 여부: (예: deny 규칙이 특정 명령을 차단했는가?)
   - 슬래시 커맨드 사용 여부: (프롬프트에서 커맨드를 참조했는가?)

## 영역 B: 파이프라인 안정성

2. 사람 개입 없이 7단계 전체를 완료한 횟수:
   - 시도 횟수: ___ 회
   - 성공 횟수: ___ 회 (자동 완료율: ___%)
   
3. 가장 많이 실패한 단계와 원인:
   - 단계: stage:N-___
   - 원인 카테고리: INFRA / DATA / AGENT / WORKFLOW

## 영역 C: BigQuery 비용 실측

4. 7단계 파이프라인 1회 실행 총 비용:
   - 총 스캔 데이터: ___ GB
   - 총 비용: $___
   - 비용 정책(1GB 제한) 준수 여부: ✅ / ❌
```

**하니스 생성**: 회고 결과를 바탕으로 다음을 실행합니다:
1. 가장 많이 실패한 단계의 `.claude/prompts/stage-N-*.md` 프롬프트에 명시적 제약 조건 추가
2. `AGENTS.md`에 "파이프라인 운영 중 발견된 실수" 섹션 추가
3. 비용이 예상보다 높은 단계가 있으면 해당 단계의 쿼리를 최적화하고 `bq-cost-guard.sh`의 임계값 재검토
