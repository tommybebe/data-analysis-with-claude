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

> ⚠️ **단일 출처 원칙**: 이 문서의 코드는 **학습용 주석(한국어)** 이 달린 참조 구현입니다. 실제로 실행되는 정본 파일은 각 모듈 디렉터리(`module-N-*/.claude/hooks/`, `.claude/commands/`, `.github/workflows/` 등)에 있습니다. 동작 검증·수정은 모듈 디렉터리의 파일을 기준으로 하세요.

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
# bq-cost-guard.sh — BigQuery 쿼리 비용 가드
# 훅 타입: PreToolUse
# 매처: Bash (bq query 명령 감지)
# 역할: bq query 실행 전 dry-run으로 예상 스캔 바이트 확인 → 한도 초과 시 차단

set -euo pipefail

# 비용 한도 (기본값: 1GB, 환경변수로 조정 가능)
COST_LIMIT_BYTES="${BQ_COST_LIMIT_BYTES:-1073741824}"

# PreToolUse 훅 입력: STDIN으로 JSON 전달
# 형식: {"tool_name": "Bash", "tool_input": {"command": "..."}}
HOOK_INPUT=$(cat)
TOOL_INPUT=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# tool_input.command 키 확인
cmd = data.get('tool_input', {}).get('command', '') or data.get('command', '')
print(cmd)
" 2>/dev/null || echo "")

# bq query 명령이 아니면 통과 (다른 Bash 명령은 허용)
if [[ "$TOOL_INPUT" != *"bq query"* ]]; then
    exit 0
fi

# --dry_run 플래그가 이미 포함된 경우 통과 (dry-run 자체는 허용)
if [[ "$TOOL_INPUT" == *"--dry_run"* ]]; then
    exit 0
fi

# 쿼리 추출
QUERY=$(echo "$TOOL_INPUT" | sed "s/.*bq query[^'\"]*['\"]//;s/['\"].*//")

if [[ -z "$QUERY" ]]; then
    echo "⚠️  [bq-cost-guard] 쿼리 파싱 불가 — 수동으로 비용 확인하세요." >&2
    exit 0
fi

# dry-run으로 예상 스캔 바이트 확인
echo "🔍 [bq-cost-guard] dry-run 실행 중..." >&2
DRY_RUN_OUTPUT=$(bq query --dry_run --use_legacy_sql=false "$QUERY" 2>&1) || {
    echo "❌ [bq-cost-guard] dry-run 실패: $DRY_RUN_OUTPUT" >&2
    exit 1
}

# 스캔 바이트 추출
BYTES=$(echo "$DRY_RUN_OUTPUT" | python3 -c "
import json, sys, re
output = sys.stdin.read()
try:
    data = json.loads(output)
    print(data.get('statistics', {}).get('totalBytesProcessed', '0'))
except:
    match = re.search(r'totalBytesProcessed[\":\s]+([0-9]+)', output)
    print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

BYTES=${BYTES:-0}

# 사람이 읽기 쉬운 크기 표현
if [[ "$BYTES" -gt 1073741824 ]]; then
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1073741824:.2f} GB')")"
elif [[ "$BYTES" -gt 1048576 ]]; then
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1048576:.2f} MB')")"
else
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1024:.2f} KB')")"
fi

# 예상 비용 ($5/TB 기준)
COST_USD=$(python3 -c "print(f'\${$BYTES/1099511627776*5:.4f}')" 2>/dev/null || echo "\$0.0000")

echo "📊 [bq-cost-guard] 예상 스캔: $HUMAN_SIZE | 예상 비용: $COST_USD" >&2

# 한도 초과 시 차단 (exit 1)
if [[ "$BYTES" -gt "$COST_LIMIT_BYTES" ]]; then
    LIMIT_HUMAN="$(python3 -c "print(f'{$COST_LIMIT_BYTES/1073741824:.2f} GB')")"
    echo "❌ [bq-cost-guard] 비용 한도 초과! (한도: $LIMIT_HUMAN, 예상: $HUMAN_SIZE)" >&2
    echo "   최적화: WHERE 절 날짜 파티션 필터, mart 모델(fct_*) 활용" >&2
    exit 1  # Claude Code가 bq query 실행을 취소함
fi

echo "✅ [bq-cost-guard] 비용 한도 이내 — 쿼리 실행 허용" >&2
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

# 기대 출력: "❌ [bq-cost-guard] 비용 한도 초과!" 메시지와 exit 1
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
# dbt-auto-test.sh — dbt 모델 편집 후 자동 컴파일 검증
# 훅 타입: PostToolUse
# 매처: Write / Edit (models/**/*.sql 파일)
# 역할: dbt SQL 파일 수정 시 즉각 문법 오류 피드백 제공

set -uo pipefail

# PostToolUse 입력에서 수정된 파일 경로 추출
HOOK_INPUT=$(cat)
FILE_PATH=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# tool_input.file_path 또는 path 키
path = data.get('tool_input', {}).get('file_path', '') or \
       data.get('tool_input', {}).get('path', '')
print(path)
" 2>/dev/null || echo "")

# dbt 모델 파일이 아니면 통과
if [[ "$FILE_PATH" != *"models/"*".sql" ]]; then
    exit 0
fi

echo "🔧 [dbt-auto-test] dbt 모델 변경 감지: $FILE_PATH" >&2
echo "   dbt compile 실행 중..." >&2

# dbt compile로 SQL 문법 검증 (빌드 없이 SQL 생성만 시도)
if dbt compile 2>&1 | tail -5 >&2; then
    echo "✅ [dbt-auto-test] dbt compile 성공 — SQL 문법 정상" >&2
    exit 0
else
    echo "❌ [dbt-auto-test] dbt compile 실패 — SQL 문법 오류 확인 필요" >&2
    exit 1  # Claude Code가 오류를 확인하도록 알림
fi
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
      "Bash(dbt source freshness:*)",
      "Bash(dbt ls:*)",
      "Bash(dbt deps:*)",
      "Bash(dbt debug:*)",
      "Bash(bq query --dry_run:*)",
      "Bash(bq show:*)",
      "Bash(bq ls:*)",
      "Bash(uv run:*)",
      "Bash(git diff:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout -b:*)",
      "Bash(git push:*)",
      "Bash(gh issue view:*)",
      "Bash(gh issue list:*)",
      "Bash(gh pr create:*)",
      "Bash(gh pr list:*)",
      "Bash(python3:*)",
      "Bash(jq:*)",
      "Read",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push origin main:*)",
      "Bash(git push origin master:*)",
      "Bash(bq rm:*)",
      "Bash(bq mk --force:*)",
      "Bash(dbt run --full-refresh:*)",
      "Bash(rm -rf:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }
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
# stop-summary.sh — 세션 종료 시 작업 요약 생성
# 훅 타입: Stop
# 역할: 에이전트 세션의 가시성 확보 — 무엇이 변경되었는지 자동 기록

set -uo pipefail

# 증거 디렉토리 생성 (없으면)
mkdir -p evidence

# 현재 시각과 Git 변경 사항 수집
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
GIT_CHANGES=$(git diff --name-only HEAD 2>/dev/null | head -20 || echo "")
STAGED_CHANGES=$(git diff --cached --name-only 2>/dev/null | head -20 || echo "")

# JSON 형식으로 세션 요약 저장
python3 - << PYEOF
import json, os
from datetime import datetime

# 기존 로그 로드 (있으면)
log_file = "evidence/session_log.json"
sessions = []
if os.path.exists(log_file):
    try:
        with open(log_file) as f:
            sessions = json.load(f)
    except:
        sessions = []

# 새 세션 항목 추가
session = {
    "timestamp": "${TIMESTAMP}",
    "git_changes": """${GIT_CHANGES}""".strip().split('\n') if """${GIT_CHANGES}""".strip() else [],
    "staged_changes": """${STAGED_CHANGES}""".strip().split('\n') if """${STAGED_CHANGES}""".strip() else []
}
sessions.append(session)

# 최근 50개 세션만 유지
sessions = sessions[-50:]

with open(log_file, 'w') as f:
    json.dump(sessions, f, indent=2, ensure_ascii=False)

print(f"✅ [stop-summary] 세션 요약 저장: {log_file} ({len(sessions)}개 항목)")
PYEOF

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

이 커맨드는 커맨드 파일 구조를 이해하기 위한 예제입니다.

## 입력

- `$ARGUMENTS`: 인사 대상 이름 (예: `/hello FitTrack팀`)

## 실행 단계

### 1단계: 인사말 출력
현재 시각과 `$ARGUMENTS`에 입력된 이름을 포함한 인사말을 출력합니다.

### 2단계: 프로젝트 상태 요약
`AGENTS.md`를 읽고 프로젝트명과 주요 구성 요소(BigQuery, dbt, marimo)를 한 줄로 요약합니다.

## 출력

```
안녕하세요, [이름]! [현재 시각]
프로젝트: FitTrack 데이터 분석 — BigQuery + dbt + marimo 기반
```

## 제약 조건

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
# /analyze — 분석 요청 → end-to-end 데이터 분석 실행

GitHub Issue 또는 분석 요청 텍스트를 받아 dbt 모델 확인 → 쿼리 설계 →
marimo 노트북 생성 → 완료 증거 저장까지 전 과정을 수행합니다.

## 입력

- `$ARGUMENTS`: 다음 중 하나
  - GitHub Issue 번호: `#42` 형식
  - 분석 요청 텍스트: `"[지표] [기간] [세그먼트(선택)]"` 형식
    - 예: `"2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"`

## 실행 단계

### 1단계: 분석 요청 파싱
- GitHub Issue 번호인 경우: `gh issue view $ISSUE_NUMBER` 실행하여 본문 확인
- 텍스트인 경우: 직접 파싱
- 추출 항목: 지표, 기간(시작일~종료일), 세그먼트, 기대 산출물

### 2단계: 기존 dbt 모델 탐색
`models/` 디렉토리에서 사용 가능한 mart 모델 확인:
- `fct_daily_active_users` — DAU 일별 집계
- `fct_monthly_active_users` — MAU 월별 집계
- `fct_retention_cohort` — 코호트 리텐션
기존 모델로 분석 가능하면 재사용, 불가능할 경우만 신규 모델 작성.

### 3단계: 비용 사전 검증 (필수)
새 쿼리가 필요한 경우 반드시 dry-run으로 비용 확인:
```bash
bq query --dry_run --use_legacy_sql=false "[SQL]"
```
예상 스캔량과 비용($5/TB 기준)을 출력합니다.
1GB 초과 시 쿼리 최적화(파티션 필터, SELECT * 제거, mart 재사용) 후 재확인.

### 4단계: dbt 모델 작성 (필요 시만)
기존 mart로 충분하지 않은 경우에만:
- `models/marts/` 하위에 `fct_` 또는 `dim_` 접두사로 파일 생성
- `schema.yml`에 `unique` + `not_null` 테스트 추가
- `dbt run --select [모델명]`으로 빌드 확인

### 5단계: marimo 노트북 생성
파일 경로: `analyses/analysis_[지표]_[YYYYMM].py`
구조 (순서대로):
1. 분석 제목·기간·핵심 발견 요약 (`mo.md` 셀)
2. BigQuery 연결 및 데이터 로드
3. 데이터 변환·집계 계산
4. 시각화 (plotly 또는 altair)
5. 결론 및 제안 (`mo.md` 셀)

### 6단계: 완료 증거 저장
`evidence/query_cost_log.json`에 실행된 쿼리의 비용 정보 기록:
```json
{
  "timestamp": "[ISO 8601]",
  "analysis_topic": "[분석 주제]",
  "queries": [
    {
      "sql_preview": "[SQL 앞 100자]",
      "estimated_bytes": 0,
      "cost_usd": 0.0,
      "within_threshold": true
    }
  ]
}
```

## marimo 노트북 작성 규약

- 차트 제목·축 레이블·범례: **한국어**
- 숫자: 천 단위 쉼표, 비율은 소수점 2자리 (%)
- BigQuery 연결: `google.cloud.bigquery.Client(project=os.environ["BQ_PROJECT_ID"])`
- 변수명·함수명: 영어, 주석: 한국어

## 출력

분석 완료 후:
```
## 분석 완료

### 생성된 파일
- 📓 analyses/analysis_[주제]_[기간].py
- 📦 models/marts/fct_[이름].sql (신규 모델이 있을 경우)

### BigQuery 비용
- 예상 스캔량: X.X GB
- 예상 비용: $X.XXXX USD (on-demand $5/TB 기준)

### dbt 테스트
- ✅ N개 통과 / ❌ N개 실패
```

## 제약 조건

- **금지**: 쿼리 비용 사전 확인 없이 bq query 실행
- **금지**: `staging/` 레이어 직접 쿼리 (mart 모델 기반으로 작성)
- **금지**: 기존 marimo 노트북 파일 덮어쓰기 (새 파일명 생성)
- **필수**: `analyses/` 경로로 노트북 저장
- **필수**: 완료 증거 JSON 저장 (`evidence/query_cost_log.json`)
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
# /check-cost — BigQuery 쿼리 비용 사전 확인

SQL 쿼리를 입력받아 BigQuery dry-run으로 예상 스캔량과 비용을 조회합니다.
실제 쿼리 실행 전에 비용을 확인하는 습관을 위한 커맨드입니다.

## 입력

- `$ARGUMENTS`: 비용을 확인할 SQL 쿼리 텍스트
  - 예: `SELECT COUNT(*) FROM \`project.dataset.fct_daily_active_users\``

## 실행 단계

### 1단계: dry-run 실행
```bash
bq query --dry_run --use_legacy_sql=false "$ARGUMENTS"
```

### 2단계: 비용 계산 및 판정
스캔 바이트 수를 가져와 다음 기준으로 판정:
- **✅ 안전 범위**: 1GB 미만 — 예상 비용 $0.005 미만
- **⚠️ 주의 (1~10GB)**: 최적화 검토 권장 — 예상 비용 $0.005~$0.05
- **❌ 위험 (10GB 초과)**: 실행 전 반드시 재검토 필요 — 예상 비용 $0.05 이상

### 3단계: 최적화 제안 (주의/위험 판정 시)
비용이 높을 경우:
1. WHERE 절에 날짜 파티션 필터(`_PARTITIONDATE`) 추가
2. `SELECT *` 대신 필요한 컬럼만 명시
3. mart 모델(`fct_*`) 사용으로 사전 집계 데이터 활용

## 출력

```
## BigQuery 비용 확인

**SQL 미리보기**: [SQL 앞 100자]...
**예상 스캔량**: X.XX GB (X bytes)
**예상 비용**: $X.XXXX USD (on-demand $5/TB 기준)
**판정**: ✅ 안전 범위 | ⚠️ 주의 | ❌ 위험

[주의/위험 판정 시] **최적화 제안**: ...
```

## 제약 조건

- `--dry_run` 없이 실제 쿼리를 실행하지 않음 (비용 발생 방지)
- 결과를 `evidence/query_cost_log.json`에 추가 기록
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
# /validate-models — dbt 모델 빌드·테스트 및 결과 보고

`dbt run` → `dbt test` 순서로 실행하고 결과를 요약하여 증거 파일에 저장합니다.

## 입력

- `$ARGUMENTS`: 선택적. 특정 모델 이름 지정 시 해당 모델만 실행
  - 예: `/validate-models fct_daily_active_users` — 특정 모델만
  - 빈 경우: 전체 모델 실행

## 실행 단계

### 1단계: dbt 의존성 확인
`dbt deps`를 실행하여 패키지가 설치되어 있는지 확인합니다.

### 2단계: dbt run
`$ARGUMENTS`가 있으면 `dbt run --select $ARGUMENTS`, 없으면 `dbt run` 실행.

### 3단계: dbt test
`dbt test` 실행. 실패한 테스트의 이름과 모델을 수집합니다.

### 4단계: 결과 저장
`evidence/dbt_test_results.json`에 저장:
```json
{
  "timestamp": "[ISO 8601]",
  "run_scope": "전체 | 특정 모델명",
  "total_tests": 0,
  "passed": 0,
  "failed": 0,
  "failed_tests": []
}
```

## 출력

```
## dbt 검증 결과

**실행 범위**: 전체 / [모델명]
**빌드**: ✅ N개 성공 / ❌ N개 실패
**테스트**: ✅ N개 통과 / ❌ N개 실패

[실패한 테스트가 있을 경우]
**실패 상세**:
- [테스트명]: [모델명] — [실패 원인]
```

## 제약 조건

- dbt 실패 시 중단하지 않고 전체 결과를 수집 후 보고
- 증거 파일 저장은 성공/실패 무관하게 반드시 수행
EOF

# /generate-report — marimo 노트북 → HTML/PDF 내보내기
cat > .claude/commands/generate-report.md << 'EOF'
# /generate-report — marimo 노트북을 HTML/PDF 리포트로 내보내기

marimo 노트북을 실행하여 HTML과 PDF 형식으로 내보내고 결과를 기록합니다.

## 입력

- `$ARGUMENTS`: marimo 노트북 파일 경로
  - 예: `/generate-report analyses/analysis_dau_202601.py`

## 실행 단계

### 1단계: 노트북 존재 확인
`$ARGUMENTS` 경로에 파일이 존재하는지 확인합니다.

### 2단계: HTML 내보내기
```bash
uv run marimo export html $ARGUMENTS -o reports/$(basename $ARGUMENTS .py).html
```
예상 비용: $0 (BigQuery 미사용)

### 3단계: 리포트 매니페스트 저장
`evidence/report_manifest.json`에 저장:
```json
{
  "timestamp": "[ISO 8601]",
  "notebook_source": "[노트북 파일 경로]",
  "outputs": [
    { "format": "html", "path": "reports/[파일명].html", "size_bytes": 0 }
  ]
}
```

## 출력

```
## 리포트 생성 완료

**소스**: [노트북 경로]
**생성 파일**:
- 📄 reports/[파일명].html (X KB)

**확인 방법**: 브라우저에서 HTML 파일 열기
```

## 제약 조건

- `reports/` 디렉토리가 없으면 자동 생성
- 같은 이름의 리포트 파일이 존재하면 타임스탬프를 파일명에 추가하여 덮어쓰기 방지
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
> - 커맨드 파일의 `## 입력` 섹션에서 예시 형식을 명확하게 제시하면 에이전트가 정확하게 파싱합니다
> - `$ARGUMENTS`가 비어있을 경우의 기본값 동작을 `## 제약 조건`에 명시하세요

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

> 💰 **BigQuery 비용 관련 권한**: `Bash(bq:*)` 허용 규칙은 모든 BigQuery CLI 명령을 허용합니다. 비용 제어를 위해 훅(`bq-cost-guard.sh`)과 함께 사용해야 합니다. 권한 설정만으로는 비용을 제어할 수 없습니다 — 훅이 실제 비용 가드를 담당합니다.

FitTrack 데이터 분석 에이전트에게 필요한 최소 권한을 설계합니다:

```json
{
  "permissions": {
    "allow": [
      "Bash(bq:*)",
      "Bash(bq query:*)",
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(marimo run:*)",
      "Bash(marimo export:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push origin HEAD:*)",
      "Bash(gh issue comment:*)",
      "Bash(gh issue edit --add-label:*)",
      "Bash(gh issue edit --remove-label:*)",
      "Bash(gh pr create:*)"
    ]
  }
}
```

허용 규칙 설계 원칙:
- **작업 범위 명시**: `bq:*`보다 `bq query:*`가 더 안전하지만, 유연성을 위해 `bq:*` 허용 후 `deny`로 위험 명령 차단
- **git 작업 분리**: `git push`는 허용하되, `git push --force`는 deny 목록에서 차단
- **GitHub CLI**: 이슈 관리 및 PR 생성에 필요한 `gh` 명령만 허용

다음 Claude Code 프롬프트로 권한 설계를 에이전트에게 요청합니다:

```bash
claude "현재 .claude/settings.json을 분석하고, FitTrack 데이터 분석 에이전트가
필요한 최소 권한을 permissions.allow 섹션에 추가해줘.

필요한 작업 유형:
1. BigQuery 쿼리 실행 (bq query)
2. dbt 모델 실행/테스트/컴파일 (dbt run, dbt test, dbt compile)
3. marimo 노트북 실행 및 HTML/PDF 내보내기
4. Git 작업 (add, commit, push)
5. GitHub CLI로 이슈 코멘트, 라벨 관리, PR 생성

각 규칙에 왜 이 권한이 필요한지 JSON 주석(// 형식)으로 설명하고,
최소 권한 원칙(principle of least privilege)을 적용해줘.

수정 후 python -m json.tool .claude/settings.json으로 문법 검증해줘."
```

**활동 3: 위험 작업 차단을 위한 거부 규칙(deny) 구현 및 동작 검증** *(예상 소요: 20~25분)*

되돌리기 어려운(irreversible) 작업을 차단하는 거부 규칙을 구현하고, 실제로 차단되는지 검증합니다:

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push --force-with-lease:*)",
      "Bash(git reset --hard:*)",
      "Bash(bq rm:*)",
      "Bash(bq update --schema:*)",
      "Bash(gcloud projects delete:*)",
      "Bash(gcloud iam service-accounts delete:*)",
      "Bash(rm -rf:*)",
      "Bash(gh repo delete:*)"
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
# .github/workflows/auto-analyze.yml 권한 섹션 (개념도)
name: Auto Analyze

on:
  issues:
    types: [labeled]

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    # GitHub API 접근 권한 — 최소 권한 원칙 적용
    permissions:
      issues: write        # 이슈 코멘트 작성 + 라벨 부착/제거
      contents: write      # 파일 커밋 + 브랜치 푸시
      pull-requests: write # PR 생성 + 설명 작성

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
| `Bash(bq:*)` | BigQuery CLI로 분석 쿼리 실행 |
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
# 1. 분석 요청 이슈 생성
gh issue create \
  --title "[분석] FitTrack 2026년 1분기 DAU/MAU 트렌드 분석" \
  --body "$(cat .github/ISSUE_TEMPLATE/analysis-request.md | sed 's/---//g')" \
  --label "분석요청"

# 2. 이슈 번호 확인
ISSUE_NUMBER=$(gh issue list --label "분석요청" --limit 1 --json number -q '.[0].number')
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
