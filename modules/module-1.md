# 모듈 1: 훅과 settings.json 구성 — 에이전트 정책을 코드로 구현하기

> **학습 시간**: 2~3시간
> **난이도**: 중급 (데이터 파이프라인 경험자 대상)
> **핵심 질문**: "에이전트가 BigQuery 비용 정책을 스스로 지키게 하려면 어떻게 해야 할까?"
> **학습 구조**: 관찰(觀察) → 수정(修正) → 창작(創作) 3단계 학습 사이클

---

## 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [핵심 개념: 하니스 정책 계층](#2-핵심-개념-하니스-정책-계층)
3. [1단계: 관찰 — 훅 생애주기와 설정 구조 이해](#1단계-관찰--훅-생애주기와-설정-구조-이해)
4. [2단계: 수정 — 기존 훅과 설정 조정하기](#2단계-수정--기존-훅과-설정-조정하기)
5. [3단계: 창작 — 데이터 분석 하니스 직접 구축하기](#3단계-창작--데이터-분석-하니스-직접-구축하기)
6. [오류 처리와 디버깅](#6-오류-처리와-디버깅)
7. [모듈 자기 점검 체크리스트](#7-모듈-자기-점검-체크리스트)
8. [부록: 용어 정리](#8-부록-용어-정리)

---

## 1. 사전 요구사항

이 모듈을 시작하기 전에 다음이 준비되어 있어야 합니다.

### 1.1 환경 준비 상태 확인

```
✅ 모듈 0 완료           — 로컬 개발 환경 설정 (Claude Code, uv, dbt, marimo 설치·버전 확인)
✅ BigQuery 합성 데이터   — raw_events, raw_users, raw_sessions 테이블 적재 완료
✅ dbt 모델 빌드 성공     — staging 3개 + mart 3개 모델, dbt test 0 Fail
✅ GitHub Secrets 등록   — GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_TOKEN 설정 완료
✅ .claude/ 디렉토리     — 스타터 레포에서 .claude/hooks/, .claude/commands/ 폴더 확인
```

### 1.2 사전 지식 요구사항

| 영역 | 이 모듈에서 필요한 수준 | 부족하다면 |
|------|----------------------|------------|
| Bash 스크립트 | 변수 선언, 조건문(`if`/`case`), 종료 코드(`exit 0/1`) | Bash 기초 학습 후 복귀 |
| JSON 문법 | 객체, 배열, 중첩 구조 이해 | [json.org](https://json.org) 참조 |
| BigQuery CLI (`bq`) | `bq query`, `--dry_run` 플래그 기본 사용 | 모듈 0의 BigQuery 설정 재확인 |
| dbt | `dbt run`, `dbt test` 명령, 모델 선택자(`--select`) | 모듈 0의 dbt 섹션 복습 |
| Claude Code | 기본 대화 및 도구(Bash, Read, Write, Edit) 이해 | 모듈 0 완료 확인 |

### 1.3 이 모듈에서 다루지 않는 것

- 슬래시 커맨드(slash command) 작성 → 모듈 2에서 다룹니다
- 권한(permissions) 상세 설계 → 모듈 3에서 다룹니다
- 전체 파이프라인 자동화 → 모듈 4에서 다룹니다

**하니스 vs. 파이프라인 산출물 구분**: 이 모듈에서 여러분이 만드는 것은 **하니스(harness)** — 에이전트가 올바르게 동작하도록 강제하는 훅과 설정 — 이지, BigQuery 분석 결과물이나 dbt 모델 자체가 아닙니다. 이 구분을 항상 유지하세요.

### 1.4 3단계 학습 사이클 안내

이 모듈은 **관찰(관찰) → 수정(수정) → 창작(창작)** 3단계로 구성됩니다.

```
1단계: 관찰 — 스타터 레포의 훅과 설정을 읽고 분석합니다
              "이것은 어떻게 동작하는가?"
              (예상 소요: 50~60분)

2단계: 수정 — 기존 훅과 settings.json을 목적에 맞게 수정합니다
              "이것을 내 요구에 맞게 바꾸면?"
              (예상 소요: 40~50분)

3단계: 창작 — 새 훅을 처음부터 설계하고 작성합니다
              "이것을 없는 상태에서 만들려면?"
              (예상 소요: 50~60분)
```

각 단계는 독립적으로 진행 가능하지만, 순서대로 학습할 때 가장 효과적입니다.

---

## 2. 핵심 개념: 하니스 정책 계층

### 2.1 왜 "정책"이 필요한가

경력 데이터 분석가라면 다음 상황을 경험했을 것입니다:

**문제 시나리오**: Claude Code에게 "DAU 트렌드를 분석해줘"라고 요청했더니, 에이전트가 파티션 필터 없이 전체 `raw_events` 테이블을 스캔하는 쿼리를 실행했다. 결과: **50GB 스캔, 약 $0.25 USD 비용 발생**.

매번 에이전트에게 "파티션 필터 써"라고 말하는 것은 확장되지 않습니다. **에이전트가 정책을 자동으로 지키게 만드는 것**, 이것이 하니스 엔지니어링의 핵심입니다.

### 2.2 하니스의 세 정책 계층

```
┌──────────────────────────────────────────────────────────────────────┐
│                        하니스 정책 계층                               │
├──────────────────────────────────────────────────────────────────────┤
│  계층 1: 선언적 정책 (settings.json > permissions)                    │
│    → "에이전트는 DROP TABLE을 절대 실행할 수 없다"                      │
│    → 허용/거부 패턴 목록으로 정의                                       │
├──────────────────────────────────────────────────────────────────────┤
│  계층 2: 절차적 정책 (settings.json > hooks)                          │
│    → "BigQuery 쿼리 실행 전 반드시 비용을 확인하라"                      │
│    → 훅 스크립트로 런타임에 검사                                        │
├──────────────────────────────────────────────────────────────────────┤
│  계층 3: 서술적 정책 (AGENTS.md, 슬래시 커맨드)                         │
│    → "분석 요청은 항상 날짜 범위를 명시하라"                             │
│    → 에이전트가 읽는 텍스트 지침                                        │
└──────────────────────────────────────────────────────────────────────┘
```

**이 모듈은 계층 1과 계층 2**를 다룹니다. 계층 3(AGENTS.md, 슬래시 커맨드)은 모듈 2에서 다룹니다.

### 2.3 훅(Hook)이란 무엇인가

훅(hook)이란 **Claude Code가 특정 이벤트 시점에 자동으로 실행하는 외부 스크립트**입니다. Git의 pre-commit hook과 유사한 개념이지만, Claude Code의 도구 실행 생애주기에 통합됩니다.

훅이 없는 에이전트:
```
사용자 요청 → Claude 추론 → bq query 실행 → 결과 반환
                                   ↑
                              (비용 검사 없음)
```

훅이 있는 에이전트:
```
사용자 요청 → Claude 추론 → [PreToolUse 훅: 비용 검사] → bq query 실행
                                         ↓ 한도 초과
                                   실행 차단 + 원인 메시지
```

---

## 1단계: 관찰 — 훅 생애주기와 설정 구조 이해

> **목표**: 스타터 레포에 이미 구현된 훅과 settings.json을 읽고 분석하여, 하니스가 어떻게 동작하는지 이해합니다. 이 단계에서는 코드를 **작성하지 않습니다** — 읽고 질문하고 이해합니다.

### 관찰 1-A: Claude Code 도구 실행 생애주기

Claude Code가 도구를 실행하는 전체 흐름을 먼저 이해합니다:

```
1. 사용자 메시지 입력
         ↓
2. Claude 추론 (어떤 도구를 어떻게 사용할지 결정)
         ↓
3. PreToolUse 이벤트 발생
   → 등록된 PreToolUse 훅 실행
   → 훅이 exit 1 반환 시: 도구 실행 차단
   → 훅이 exit 0 반환 시: 도구 실행 허용
         ↓ (허용된 경우)
4. 실제 도구 실행 (Bash, Read, Write, Edit, ...)
         ↓
5. PostToolUse 이벤트 발생
   → 등록된 PostToolUse 훅 실행
   → 도구 출력 + 실행 결과를 컨텍스트로 전달받음
         ↓
6. Claude 응답 생성
         ↓
7. Stop 이벤트 발생 (대화 턴 종료 시)
   → 등록된 Stop 훅 실행
   → 작업 요약, 로그 저장, 알림 등
```

**관찰 질문 1**: 에이전트가 `bq query` 명령을 실행하려 할 때, PreToolUse 훅이 `exit 1`을 반환하면 어떤 일이 일어나는가? `bq query` 명령이 실제로 서버에 전송되는가?

**관찰 질문 2**: PostToolUse 훅에서 `exit 1`을 반환하면 도구 실행이 취소되는가? (힌트: 도구는 이미 실행된 후다)

### 관찰 1-B: 훅에 전달되는 STDIN 페이로드 분석

훅 스크립트는 표준 입력(STDIN)으로 JSON 페이로드를 받습니다. 스타터 레포의 `bq-cost-guard.sh`를 열어 STDIN을 어떻게 처리하는지 확인합니다:

```bash
# 스타터 레포 훅 파일 읽기
cat .claude/hooks/bq-cost-guard.sh
```

각 이벤트 유형의 페이로드 구조를 이해합니다:

**PreToolUse 페이로드** (Bash 도구 실행 전):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "bq query --use_legacy_sql=false 'SELECT ...'"
  }
}
```

**PostToolUse 페이로드** (Write 도구 실행 후):
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "models/marts/fct_daily_active_users.sql",
    "content": "..."
  },
  "tool_response": {
    "output": "파일이 성공적으로 작성되었습니다.",
    "error": null
  }
}
```

**Stop 페이로드** (대화 턴 종료 후):
```json
{}
```

**관찰 질문 3**: PreToolUse에서 `tool_input.command`를 추출하는 파이썬 코드를 찾아라. 왜 `python3`를 쉘 스크립트 안에서 사용하는가?

**관찰 질문 4**: PostToolUse에서 수정된 파일 경로는 어느 필드에 있는가? Write 도구와 Edit 도구의 페이로드 구조가 다른가?

### 관찰 1-C: 훅 종료 코드와 그 의미

| 종료 코드 | 의미 | 에이전트에게 전달되는 것 |
|-----------|------|------------------------|
| `exit 0` | 성공 / 허용 | 훅의 stderr 출력 (컨텍스트로 포함) |
| `exit 1` | 실패 / 차단 | 훅의 stderr 출력 (Claude가 원인으로 인식) |
| `exit 2` | 정보 제공 | stderr 출력 (차단 없이 경고만 전달) |

> **중요**: PreToolUse 훅에서 `exit 1`을 반환하면 해당 도구 실행이 **완전히 차단**됩니다. PostToolUse와 Stop 훅의 종료 코드는 도구 실행 결과에 영향을 주지 않습니다.

**stderr vs stdout 출력 처리**:

```bash
# stderr(>&2)에 쓴 내용: Claude Code 컨텍스트에 포함됨
# → 에이전트가 이 메시지를 읽고 다음 행동을 결정함
echo "❌ 비용 한도 초과: 쿼리를 최적화하세요" >&2

# stdout에 쓴 내용: 현재 버전에서는 무시됨
# → 훅 디버깅 목적으로만 사용
echo "디버그: 스캔 바이트 = $BYTES"
```

이 차이가 중요한 이유: `>&2`로 보낸 메시지는 Claude가 읽어 자동으로 수정 행동을 취합니다. 잘 작성된 오류 메시지는 에이전트에게 "왜 차단되었는지"와 "어떻게 수정할 수 있는지"를 동시에 알려주는 **피드백 루프(feedback loop)**가 됩니다.

**관찰 질문 5**: 스타터 레포의 `bq-cost-guard.sh`에서 에러 메시지를 어떤 형식으로 출력하는가? 에이전트가 그 메시지를 읽고 어떤 행동을 취하도록 유도하는가?

### 관찰 1-D: settings.json 스키마 완전 해설

```bash
# 스타터 레포 settings.json 읽기
cat .claude/settings.json | python3 -m json.tool
```

최상위 스키마 구조:

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": []
  },
  "env": {
    "BQ_COST_LIMIT_BYTES": "1073741824"
  }
}
```

각 최상위 키의 역할:

| 키 | 역할 | 이 모듈에서 다루는 정도 |
|----|------|------------------------|
| `permissions` | 도구 실행 허용/거부 패턴 | 이 모듈에서 기초 소개, 모듈 3에서 심화 |
| `hooks` | 이벤트 기반 훅 스크립트 등록 | **이 모듈의 핵심** |
| `env` | 훅에서 사용할 환경 변수 | 이 모듈에서 함께 다룸 |

**`permissions` 스키마 예시**:

```json
"permissions": {
  "allow": [
    "Bash(dbt run:*)",
    "Bash(dbt test:*)",
    "Bash(bq query --dry_run:*)",
    "Read",
    "Write",
    "Edit"
  ],
  "deny": [
    "Bash(bq rm:*)",
    "Bash(DROP TABLE:*)",
    "Bash(git push --force:*)"
  ]
}
```

**`hooks` 스키마 예시** — 훅 등록 구조 이해:

```json
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
```

**훅 이벤트 객체 필드**:

| 필드 | 설명 | 필수 여부 |
|------|------|-----------|
| `matcher` | 어느 도구에 반응할지 (Bash, Read, Write, Edit, ...) | PreToolUse/PostToolUse에서 필수 |
| `hooks` | 실행할 훅 목록 (순서대로 실행) | 필수 |
| `hooks[].type` | 훅 유형, 현재는 `"command"`만 지원 | 필수 |
| `hooks[].command` | 실행할 셸 명령어 | 필수 |

> **주의**: Stop 이벤트는 `matcher` 필드가 없습니다 — 모든 대화 턴 종료에 반응합니다.

**`env` 스키마 — 훅 환경 변수**:

```json
"env": {
  "BQ_COST_LIMIT_BYTES": "1073741824",
  "BQ_PROJECT_ID": "my-analytics-project",
  "DBT_TARGET": "dev"
}
```

`env`에 정의된 변수는 모든 훅 스크립트에서 환경 변수로 접근할 수 있습니다:

```bash
# 훅 스크립트 내부에서 settings.json의 env 값 사용
COST_LIMIT="${BQ_COST_LIMIT_BYTES:-1073741824}"  # 기본값 1GB
```

**활용 패턴**: BigQuery 비용 한도를 `BQ_COST_LIMIT_BYTES`로 외부화하면, 훅 스크립트를 수정하지 않고도 `settings.json`만 변경하여 한도를 조정할 수 있습니다.

### 관찰 1-E: 스타터 레포 훅 코드 정밀 분석

스타터 레포의 `bq-cost-guard.sh` 전체를 읽으며 다음 구조를 파악합니다:

```bash
#!/usr/bin/env bash
# bq-cost-guard.sh — BigQuery 쿼리 비용 가드 (PreToolUse 훅)
# 교육적 목적: 이 훅은 하니스의 "절차적 정책" 계층을 구현합니다.
# 에이전트가 bq query를 실행하기 직전에 자동 호출되어 비용을 사전 검사합니다.

set -euo pipefail

# 환경 변수로 한도 설정 (settings.json의 env 섹션에서 주입)
COST_LIMIT_BYTES="${BQ_COST_LIMIT_BYTES:-1073741824}"  # 기본값: 1GB

# STDIN에서 PreToolUse 페이로드 읽기
HOOK_INPUT=$(cat)

# tool_input.command 추출 — Bash 도구가 실행하려는 명령어
TOOL_INPUT=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# PreToolUse Bash 도구: tool_input.command 에 실행할 명령어가 있음
cmd = data.get('tool_input', {}).get('command', '')
print(cmd)
" 2>/dev/null || echo "")

# bq query 명령이 아니면 즉시 통과 (다른 Bash 명령은 검사 불필요)
if [[ "$TOOL_INPUT" != *"bq query"* ]]; then
    exit 0
fi

# --dry_run이 이미 포함된 경우 통과 (dry-run 자체는 비용 없음)
if [[ "$TOOL_INPUT" == *"--dry_run"* ]]; then
    exit 0
fi

# 실제 쿼리를 dry-run으로 실행하여 스캔 바이트 확인
# BigQuery on-demand 비용: $5/TB = $0.000004657/MB
DRY_OUTPUT=$(bq query --dry_run --use_legacy_sql=false \
    "$(echo "$TOOL_INPUT" | sed 's/bq query[^'"'"']*//;s/'"'"'//g')" 2>&1 || echo "DRY_RUN_FAILED")

BYTES=$(echo "$DRY_OUTPUT" | python3 -c "
import re, sys
# BigQuery dry-run 출력에서 totalBytesProcessed 값 추출
output = sys.stdin.read()
match = re.search(r'(\d+) bytes processed', output)
print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

# 예상 비용 계산 ($5/TB 기준: 1TB = 1,099,511,627,776 바이트)
COST_USD=$(python3 -c "
bytes = int('${BYTES}')
cost = bytes / 1099511627776 * 5  # $5 per TB (BigQuery on-demand 가격)
gb = bytes / 1073741824
print(f'예상: {gb:.2f}GB 스캔 | 비용: \${cost:.4f} USD')
" 2>/dev/null || echo "비용 계산 실패")

echo "📊 $COST_USD" >&2

# 한도 초과 시 차단
if [[ "$BYTES" -gt "$COST_LIMIT_BYTES" ]]; then
    echo "❌ [bq-cost-guard] 비용 한도 초과! 쿼리를 최적화하세요:" >&2
    echo "   1. WHERE 절에 날짜 파티션 필터 추가 (예: event_date >= '2024-01-01')" >&2
    echo "   2. SELECT * 대신 필요한 컬럼만 명시" >&2
    echo "   3. mart 모델(fct_*) 활용으로 사전 집계 데이터 사용" >&2
    exit 1  # 실행 차단
fi

exit 0  # 실행 허용
```

**관찰 질문 6**: `set -euo pipefail`의 각 플래그가 무엇을 하는가? 훅 스크립트에서 이 설정이 특히 중요한 이유는?

**관찰 질문 7**: 훅이 BigQuery dry-run을 실행하기 위해 원본 쿼리를 어떻게 추출하는가? `sed` 명령의 역할은?

**관찰 요약**: 이제 다음을 이해했어야 합니다.
- 훅 생애주기 (PreToolUse → 실행 → PostToolUse → Stop)
- STDIN 페이로드 구조와 파싱 방법
- 종료 코드(exit 0/1)의 의미와 차이
- settings.json의 스키마 구조
- 실제 비용 가드 훅의 동작 원리

---

## 2단계: 수정 — 기존 훅과 설정 조정하기

> **목표**: 스타터 레포의 기존 훅과 settings.json을 분석 환경에 맞게 조정합니다. 이미 작동하는 코드를 변경하면서 각 파라미터의 효과를 직접 확인합니다.

### 수정 2-A: BigQuery 비용 한도 환경 변수 조정

학습 환경에서는 실수로 대용량 쿼리를 실행하더라도 비용이 제한되도록 한도를 더 낮게 설정합니다.

**현재 설정 확인**:
```bash
# 현재 비용 한도 확인
grep "BQ_COST_LIMIT_BYTES" .claude/settings.json
# 출력 예시: "BQ_COST_LIMIT_BYTES": "1073741824"  → 1GB (1,073,741,824 바이트)
```

**수정 1**: 학습 환경 한도를 500MB로 낮추기

```json
// .claude/settings.json — env 섹션 수정
// 교육적 목적: 한도를 낮춰 비용 가드 동작을 더 자주 확인할 수 있게 함
"env": {
  "BQ_COST_LIMIT_BYTES": "536870912",
  "BQ_PROJECT_ID": "your-gcp-project-id"
}
```

**검증 방법**:
```bash
# 한도를 변경 후, Claude Code에서 다음을 요청
# "raw_events 테이블에서 지난 60일 데이터를 파티션 필터 없이 조회해줘"
# 예상 결과: 훅이 더 일찍 차단됨
```

**수정 2**: BigQuery 프로젝트 ID를 환경 변수로 추가

스타터 레포의 훅 스크립트가 하드코딩된 프로젝트 ID를 사용하고 있다면, `env`에 추가하여 외부화합니다:

```json
"env": {
  "BQ_COST_LIMIT_BYTES": "536870912",
  "BQ_PROJECT_ID": "your-project-id",
  "DBT_TARGET": "dev"
}
```

훅 스크립트에서 참조:
```bash
# 훅 내부에서 환경 변수 사용 — settings.json의 env에서 주입됨
PROJECT="${BQ_PROJECT_ID:-my-default-project}"
```

### 수정 2-B: dbt 자동 테스트 훅에 Edit 매처 추가

스타터 레포의 `settings.json`에서 `dbt-auto-test.sh`가 `Write` 이벤트에만 등록되어 있을 수 있습니다. SQL 파일을 `Edit`으로 수정할 때도 테스트가 실행되도록 추가합니다.

**현재 상태 확인**:
```bash
# PostToolUse 훅 설정 확인
python3 -c "
import json
with open('.claude/settings.json') as f:
    cfg = json.load(f)
for h in cfg.get('hooks', {}).get('PostToolUse', []):
    print(h.get('matcher'), '→', [x.get('command') for x in h.get('hooks', [])])
"
```

**수정**: `Edit` 매처 추가

```json
// settings.json — PostToolUse 섹션
// 교육적 목적: Write와 Edit 두 도구 모두 dbt 테스트를 트리거해야 함
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
]
```

**검증 방법**:
```bash
# Claude Code에서 Edit 도구로 SQL 파일 수정을 요청
# "stg_events.sql 파일에서 컬럼 주석을 업데이트해줘"
# 예상 결과: 파일 수정 직후 "🧪 [dbt-auto-test]" 메시지 출력됨
```

### 수정 2-C: 오류 메시지 품질 개선

스타터 레포의 비용 가드 훅 오류 메시지를 프로젝트 도메인에 맞게 개선합니다.

**원본 오류 메시지**:
```bash
echo "❌ 비용 한도 초과! 쿼리를 최적화하세요" >&2
```

**수정 후 도메인 특화 메시지**:
```bash
# bq-cost-guard.sh의 오류 메시지 섹션 수정
# 교육적 목적: 구체적인 대안 제시가 에이전트의 자동 수정 성공률을 높임
echo "❌ [bq-cost-guard] 비용 한도 초과 (한도: ${COST_LIMIT_BYTES} 바이트)" >&2
echo "   이 프로젝트에서 허용된 쿼리 패턴:" >&2
echo "   1. fct_daily_active_users에서 조회 (예상 비용: ~$0.025/30일)" >&2
echo "   2. stg_events에서 event_date 파티션 필터 필수 사용" >&2
echo "   3. raw_events 직접 스캔 금지 (전체 스캔 시 ~$2.50)" >&2
echo "   ↑ AGENTS.md의 '아키텍처 규약' 섹션을 참조하세요" >&2
exit 1
```

**수정의 원칙**: 에이전트에게 "무엇이 잘못되었는지"뿐 아니라 "어떻게 고쳐야 하는지"를 함께 알려주면, 에이전트가 자동으로 올바른 방향으로 수정합니다.

### 수정 2-D: dbt 모델 선택자 로직 개선

`dbt-auto-test.sh`의 모델 선택자를 확인하고 필요에 따라 조정합니다.

```bash
# 현재 dbt-auto-test.sh에서 사용하는 선택자 확인
grep "dbt test" .claude/hooks/dbt-auto-test.sh
```

**현재 선택자**: `dbt test --select "${MODEL_NAME}+"`

`+` 연산자의 의미:
```
fct_daily_active_users+
    → fct_daily_active_users 모델
    → fct_daily_active_users에 의존하는 모든 하위 모델
    → fct_monthly_active_users (MAU = f(DAU)이므로)
```

**수정**: staging 모델 수정 시 상위 테스트도 포함

staging 모델을 수정할 때는 해당 모델의 상류(upstream) 소스 테스트도 함께 실행하도록 선택자를 조정합니다:

```bash
# staging 모델인 경우 상류 포함, mart 모델인 경우 하류 포함
if [[ "$MODEL_NAME" == stg_* ]]; then
    # staging 모델: 자신과 하위 모델만 테스트
    SELECTOR="${MODEL_NAME}+"
else
    # mart 모델: 자신의 상위 staging 모델도 포함
    SELECTOR="+${MODEL_NAME}+"
fi
echo "🧪 [dbt-auto-test] ${SELECTOR} 테스트 실행 중..." >&2
uv run dbt test --select "$SELECTOR" 2>&1 || true
```

**수정 요약**: 이 단계에서 변경한 항목들:
1. `BQ_COST_LIMIT_BYTES`: 1GB → 500MB (학습 환경 최적화)
2. `BQ_PROJECT_ID`: env에 추가 (하드코딩 제거)
3. PostToolUse: `Edit` 매처 추가 (테스트 커버리지 향상)
4. 오류 메시지: 도메인 특화 안내 포함 (자동 수정 성공률 향상)
5. dbt 선택자: staging/mart 구분 로직 개선

---

## 3단계: 창작 — 데이터 분석 하니스 직접 구축하기

> **목표**: 스타터 레포에 없는 새 훅을 처음부터 설계하고 구현합니다. 2단계까지의 이해를 바탕으로, 패턴만 제공하고 세부 구현은 직접 작성합니다.

### 창작 3-A: 작업 완료 요약 훅 구현 (Stop 훅)

**목표**: Claude Code가 작업을 마칠 때마다 자동으로 변경 사항, 테스트 결과, BigQuery 비용 누계를 요약하는 Stop 훅을 처음부터 구현합니다.

**설계 요구사항**:
- 변경된 파일 목록 (git status)
- 이번 세션의 BigQuery 비용 누계 (`.claude/logs/query-log.jsonl` 활용)
- dbt 테스트 결과 요약 (`target/run_results.json` 활용)
- Stop 훅이므로 항상 `exit 0` 반환

**기본 구조 (이 구조에서 시작하여 직접 완성하세요)**:

```bash
#!/usr/bin/env bash
# stop-summary.sh — 작업 완료 요약 (Stop 훅)
# 교육적 목적: Stop 훅은 에이전트의 작업을 가시화하는 "관찰 가능성(observability)" 패턴을 구현합니다.
# Stop 훅이므로 항상 exit 0 — 대화 종료를 차단하지 않음

# ─────────────────────────────────────────────────
# 1. 변경된 파일 목록
# ─────────────────────────────────────────────────
CHANGED=$(git status --short 2>/dev/null || echo "")

echo "📋 ─────────────── 작업 완료 요약 ───────────────" >&2

if [[ -n "$CHANGED" ]]; then
    echo "📝 변경된 파일:" >&2
    echo "$CHANGED" | while read -r line; do
        echo "   $line" >&2
    done
else
    echo "   (변경된 파일 없음)" >&2
fi

# ─────────────────────────────────────────────────
# 2. dbt 테스트 결과 요약
# ─────────────────────────────────────────────────
DBT_RESULTS="target/run_results.json"
if [[ -f "$DBT_RESULTS" ]]; then
    python3 -c "
import json, sys
with open('$DBT_RESULTS') as f:
    results = json.load(f)
# run_results.json에서 테스트 결과 집계
statuses = [r.get('status') for r in results.get('results', [])]
passed = statuses.count('pass')
failed = statuses.count('fail')
warn = statuses.count('warn')
total = len(statuses)
icon = '✅' if failed == 0 else '❌'
print(f'{icon} dbt 테스트: {total}개 중 통과 {passed}개, 실패 {failed}개, 경고 {warn}개')
" >&2 2>/dev/null || echo "   (dbt 테스트 결과 없음)" >&2
fi

# ─────────────────────────────────────────────────
# 3. BigQuery 비용 누계
# ─────────────────────────────────────────────────
LOG_FILE=".claude/logs/query-log.jsonl"
if [[ -f "$LOG_FILE" ]]; then
    TODAY=$(date +%Y-%m-%d)
    # 오늘 세션의 누계 비용 계산
    grep "$TODAY" "$LOG_FILE" 2>/dev/null | python3 -c "
import sys, json
lines = [l for l in sys.stdin if l.strip()]
if not lines:
    print('   (오늘 BigQuery 쿼리 없음)')
    sys.exit(0)
total_bytes = sum(json.loads(l).get('bytes_processed', 0) for l in lines)
total_cost = sum(json.loads(l).get('cost_usd', 0) for l in lines)
# 비용 단위: $5/TB (BigQuery on-demand 가격)
print(f'💰 오늘 BigQuery 누계: {total_bytes/1e9:.2f}GB | 비용: \${total_cost:.4f} USD ({len(lines)}건)')
" >&2 2>/dev/null || echo "   (비용 로그 파싱 실패)" >&2
fi

echo "📋 ────────────────────────────────────────────" >&2

exit 0  # Stop 훅은 항상 exit 0
```

**settings.json에 Stop 훅 등록**:

```json
// settings.json — Stop 섹션 추가
// 교육적 목적: Stop 훅은 matcher 없이 등록 — 모든 대화 턴 종료에 실행됨
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
```

**검증 방법**:
```bash
# 1. 스크립트 실행 권한 설정
chmod +x .claude/hooks/stop-summary.sh

# 2. 직접 실행 테스트
bash .claude/hooks/stop-summary.sh < /dev/null
echo "종료 코드: $?"
# 예상 출력: "📋 ─────────── 작업 완료 요약 ───────────" 와 함께 git status

# 3. Claude Code 세션에서 테스트
# "stg_events.sql 파일을 읽어줘" 요청 후 대화 완료
# 예상 결과: 대화 종료 시 요약이 자동 출력됨
```

### 창작 3-B: BigQuery 비용 로거 구현 (PostToolUse 훅)

**목표**: Bash 도구 실행 후 BigQuery 쿼리 비용을 JSONL 파일에 자동 기록하는 PostToolUse 훅을 작성합니다. Stop 훅의 비용 누계 계산에 사용됩니다.

**요구사항**:
- `bq query`를 실행한 경우에만 기록 (다른 Bash 명령은 무시)
- `.claude/logs/query-log.jsonl`에 JSONL 형식으로 추가
- 기록 형식: `{"timestamp": "...", "bytes_processed": ..., "cost_usd": ..., "query_snippet": "..."}`

**직접 구현 시작**:

```bash
#!/usr/bin/env bash
# query-logger.sh — BigQuery 쿼리 비용 로거 (PostToolUse 훅)
# 교육적 목적: PostToolUse 훅으로 에이전트 행동의 "관찰 가능성"을 구현합니다.
# bq query 실행 후 자동 호출되어 비용 데이터를 누적 기록합니다.

HOOK_INPUT=$(cat)

# PostToolUse Bash 페이로드에서 실행된 명령어와 출력 추출
COMMAND=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# PostToolUse: tool_input.command 에 실행된 명령어
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")

# bq query 명령이 아니면 무시
if [[ "$COMMAND" != *"bq query"* ]]; then
    exit 0
fi

# 로그 디렉토리 생성
mkdir -p .claude/logs

# 쿼리 스니펫 (처음 100자) 추출
SNIPPET=$(echo "$COMMAND" | head -c 100 | tr '\n' ' ')

# 실제 스캔 바이트는 PostToolUse의 tool_response.output에서 추출
# BigQuery 출력에 "bytes processed" 정보가 포함될 수 있음
OUTPUT=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_response', {}).get('output', ''))
" 2>/dev/null || echo "")

# 바이트 수 파싱 (BigQuery 출력 형식에 따라 조정 필요)
BYTES=$(echo "$OUTPUT" | python3 -c "
import re, sys
text = sys.stdin.read()
match = re.search(r'(\d+) bytes processed', text)
print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

# 비용 계산 ($5/TB, BigQuery on-demand)
COST=$(python3 -c "
b = int('${BYTES}')
print(f'{b / 1099511627776 * 5:.6f}')
" 2>/dev/null || echo "0")

# JSONL 형식으로 로그 추가
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >> ".claude/logs/query-log.jsonl" << EOF
{"timestamp": "${TIMESTAMP}", "bytes_processed": ${BYTES}, "cost_usd": ${COST}, "query_snippet": "${SNIPPET}"}
EOF

exit 0  # PostToolUse 훅은 항상 exit 0
```

**settings.json에 PostToolUse 로거 추가**:

```json
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
  },
  {
    "matcher": "Bash",
    "hooks": [
      { "type": "command", "command": "bash .claude/hooks/query-logger.sh" }
    ]
  }
]
```

### 창작 3-C: 완성된 settings.json 조합하기

관찰 → 수정 → 창작 단계를 통해 완성한 세 가지 패턴을 하나의 `settings.json`으로 통합합니다.

**세 가지 패턴**:
- 패턴 A (비용 보호): PreToolUse `bq-cost-guard.sh`
- 패턴 B (데이터 품질 피드백 루프): PostToolUse `dbt-auto-test.sh`
- 패턴 C (작업 가시성): Stop `stop-summary.sh` + PostToolUse `query-logger.sh`

```json
{
  "permissions": {
    "allow": [
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(bq query --dry_run:*)",
      "Bash(bq show:*)",
      "Bash(bq ls:*)",
      "Bash(uv run marimo export:*)",
      "Bash(git diff:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout -b:*)",
      "Bash(gh issue comment:*)",
      "Bash(gh pr create:*)",
      "Read",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(bq rm:*)",
      "Bash(bq mk --force:*)",
      "Bash(dbt run --full-refresh:*)",
      "Bash(git push --force:*)",
      "Bash(git push origin main:*)",
      "Bash(DROP TABLE:*)",
      "Bash(DELETE FROM:*)",
      "Bash(rm -rf:*)"
    ]
  },
  "env": {
    "BQ_COST_LIMIT_BYTES": "536870912",
    "BQ_PROJECT_ID": "your-gcp-project-id",
    "DBT_TARGET": "dev"
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
          { "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" },
          { "type": "command", "command": "bash .claude/hooks/marimo-check.sh" }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" },
          { "type": "command", "command": "bash .claude/hooks/marimo-check.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/query-logger.sh" }
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

**검증**:
```bash
# 1. JSON 문법 검사
python3 -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 OK"

# 2. 모든 훅 파일 실행 권한 확인
ls -la .claude/hooks/*.sh

# 3. 훅 파일 존재 여부 확인
for hook in bq-cost-guard.sh dbt-auto-test.sh query-logger.sh stop-summary.sh; do
    test -f ".claude/hooks/$hook" && echo "✅ $hook" || echo "❌ $hook 없음"
done
```

### 창작 3-D: 고급 과제 — marimo 문법 검사 훅 (자율 구현)

스타터 레포의 `settings.json`에는 `marimo-check.sh`가 참조되지만, 아직 구현되지 않았습니다. 다음 요구사항으로 직접 구현하세요:

**요구사항**:
- PostToolUse Write/Edit 이벤트에서 `.py` 파일 수정 시 실행
- `notebooks/` 디렉토리의 파일만 대상
- `uv run python -c "import ast; ast.parse(open('파일').read())"` 로 문법 검사
- 문법 오류 시 stderr에 오류 위치와 수정 방법 출력 (exit 0 — 차단 아님, 경고만)

**힌트**:
```bash
# dbt-auto-test.sh 구조를 참고하되, 다음을 변경합니다:
# 1. 파일 확장자 조건: *.sql → *.py
# 2. 디렉토리 조건: models/ → notebooks/
# 3. 실행 명령: dbt test → python3 -c "import ast; ..."
```

---

## 6. 오류 처리와 디버깅

### 6.1 훅이 실행되지 않을 때 확인 사항

```bash
# 1. 스크립트 실행 권한 확인
ls -la .claude/hooks/
# -rw-r--r-- 이면 실행 불가 → chmod +x 필요
chmod +x .claude/hooks/*.sh

# 2. settings.json 문법 확인
cat .claude/settings.json | python3 -m json.tool
# SyntaxError가 없어야 함

# 3. 훅 스크립트 직접 테스트
echo '{"tool_name":"Bash","tool_input":{"command":"bq query SELECT 1"}}' | \
  bash .claude/hooks/bq-cost-guard.sh
```

### 6.2 일반적인 오류와 해결책

| 오류 증상 | 원인 | 해결책 |
|-----------|------|--------|
| 훅이 실행되지 않음 | 실행 권한 없음 | `chmod +x .claude/hooks/*.sh` |
| settings.json 로드 실패 | JSON 문법 오류 | `python3 -m json.tool .claude/settings.json`으로 검증 |
| dry-run 실패 | GCP 인증 미설정 | `gcloud auth application-default login` 실행 |
| 훅이 항상 exit 1 | STDIN 파싱 오류 | `echo '...' | bash 훅.sh`로 직접 테스트 |
| Python 파싱 오류 | python3 미설치 | `which python3` 확인, uv 환경 활성화 |

### 6.3 훅 디버깅 모드

개발 중에는 다음 패턴으로 훅을 디버깅합니다:

```bash
# 디버깅용 테스트 페이로드 생성
cat > /tmp/test-hook-input.json << 'EOF'
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM analytics.raw_events'"
  }
}
EOF

# 훅 직접 실행
bash .claude/hooks/bq-cost-guard.sh < /tmp/test-hook-input.json
echo "종료 코드: $?"
```

---

## 7. 모듈 자기 점검 체크리스트

이 모듈을 완료했는지 아래 체크리스트로 확인하세요. 각 항목은 **명확한 합격/불합격 기준**이 있습니다.

### 관찰 단계 이해 체크리스트

- [ ] **훅 생애주기**: PreToolUse, PostToolUse, Stop 각각이 언제 실행되는지 말로 설명할 수 있다
  - ✅ 합격: "PreToolUse는 도구 실행 직전, PostToolUse는 직후, Stop은 대화 턴 종료 후"
  - ❌ 불합격: 순서가 헷갈리거나 이벤트 이름만 암기

- [ ] **종료 코드 의미**: exit 0과 exit 1의 차이, PreToolUse와 PostToolUse에서의 차이를 설명할 수 있다
  - ✅ 합격: "PreToolUse exit 1은 도구 실행 차단, PostToolUse exit 1은 경고만 (차단 권장 안 함)"
  - ❌ 불합격: 두 컨텍스트를 구분 못 함

- [ ] **STDIN 페이로드**: 각 훅 이벤트에서 받는 JSON 구조를 설명할 수 있다
  - ✅ 합격: "PreToolUse Bash: tool_input.command, PostToolUse Write: tool_input.file_path"
  - ❌ 불합격: JSON 구조 모름

- [ ] **stderr vs stdout**: 에이전트에게 피드백을 전달하려면 어떤 출력 스트림을 사용해야 하는지 알고 있다
  - ✅ 합격: "stderr(>&2)로 출력해야 Claude가 읽음"
  - ❌ 불합격: stdout으로만 출력

### 수정 단계 구현 체크리스트

- [ ] **비용 한도 조정**: `settings.json`의 `BQ_COST_LIMIT_BYTES`를 변경하고 훅 동작이 달라지는지 확인함
  - ✅ 합격: 500MB 한도에서 600MB 쿼리 시도 시 차단됨을 확인
  - ❌ 불합격: 변수 변경 후 동작 확인 안 함

- [ ] **Edit 매처 추가**: PostToolUse에 `Edit` 매처를 추가하여 SQL 편집 시에도 테스트가 실행됨을 확인
  - ✅ 합격: Edit 도구로 SQL 파일 수정 시 "🧪 [dbt-auto-test]" 메시지 출력됨
  - ❌ 불합격: Write 이벤트만 테스트 트리거

### 창작 단계 구현 체크리스트

- [ ] **settings.json 구성**: `.claude/settings.json`에 PreToolUse, PostToolUse, Stop 훅이 모두 등록되어 있다
  - ✅ 합격: `cat .claude/settings.json | python3 -m json.tool`이 오류 없이 통과
  - ❌ 불합격: JSON 문법 오류 또는 훅 누락

- [ ] **bq-cost-guard.sh 동작**: Claude Code에서 파티션 필터 없는 대용량 쿼리를 요청했을 때 훅이 실행을 차단한다
  - ✅ 합격: "❌ [bq-cost-guard] 비용 한도 초과!" 메시지가 표시되고 쿼리가 실행되지 않음
  - ❌ 불합격: 훅이 실행되지 않거나 차단 없이 쿼리가 실행됨

- [ ] **dbt-auto-test.sh 동작**: SQL 파일 수정 후 자동으로 dbt test가 실행된다
  - ✅ 합격: 에이전트가 `.sql` 파일을 수정한 직후 "🧪 [dbt-auto-test]" 메시지가 출력됨
  - ❌ 불합격: 수동으로 `dbt test` 실행해야 함

- [ ] **stop-summary.sh 동작**: 작업 완료 후 변경 파일 목록과 BigQuery 비용 누계가 자동 출력된다
  - ✅ 합격: "📋 작업 완료 요약" 섹션이 자동으로 출력됨
  - ❌ 불합격: 요약 없이 대화가 종료됨

- [ ] **실행 권한**: 모든 훅 스크립트에 실행 권한이 있다
  - ✅ 합격: `ls -la .claude/hooks/*.sh`에서 모든 파일이 `-rwxr-xr-x` 권한
  - ❌ 불합격: `-rw-r--r--` 권한 (실행 불가)

### 심화 체크리스트 (선택)

- [ ] **비용 로그 확인**: `.claude/logs/query-log.jsonl`을 열어 오늘 실행한 쿼리의 비용 누계를 계산
- [ ] **훅 직접 테스트**: 테스트 페이로드를 만들어 `bash 훅.sh < 페이로드.json`으로 훅을 직접 실행하고 종료 코드 확인
- [ ] **marimo-check.sh 구현**: 창작 3-D의 자율 과제를 완성하고 동작 확인

### 다음 모듈 진입 기준

**모든 창작 단계 구현 체크리스트 항목을 통과**해야 모듈 2로 진행할 수 있습니다. 특히 다음 두 가지는 이후 모듈의 전제 조건입니다:

1. `settings.json`에 세 가지 훅 이벤트가 모두 등록되어 있을 것
2. `bq-cost-guard.sh`가 대용량 쿼리를 실제로 차단할 것

---

## 8. 부록: 용어 정리

| 한국어 용어 | 영어 원어 | 설명 |
|-------------|-----------|------|
| 훅 (hook) | hook | 특정 이벤트 시점에 자동으로 실행되는 스크립트 |
| 훅 생애주기 (hook lifecycle) | hook lifecycle | PreToolUse → 도구 실행 → PostToolUse → Stop의 실행 흐름 |
| 사전 도구 사용 훅 (pre-tool-use hook) | PreToolUse hook | 도구 실행 직전에 실행되는 훅 |
| 사후 도구 사용 훅 (post-tool-use hook) | PostToolUse hook | 도구 실행 직후에 실행되는 훅 |
| 정지 훅 (stop hook) | Stop hook | 대화 턴 종료 시 실행되는 훅 |
| 매처 (matcher) | matcher | 훅이 반응할 도구 유형을 지정하는 패턴 |
| 페이로드 (payload) | payload | 훅에 STDIN으로 전달되는 JSON 데이터 |
| 비용 가드 (cost guard) | cost guard | 비용 한도 초과 실행을 사전에 차단하는 훅 패턴 |
| 피드백 루프 (feedback loop) | feedback loop | 훅이 에이전트의 행동을 수정하도록 유도하는 자동화 사이클 |
| 관찰 가능성 (observability) | observability | 에이전트의 작업 내역과 비용을 추적 가능하게 만드는 특성 |
| 하니스 정책 (harness policy) | harness policy | 에이전트가 준수해야 하는 규칙을 settings.json으로 구현한 것 |
| 선언적 정책 (declarative policy) | declarative policy | permissions 목록으로 정의하는 허용/거부 규칙 |
| 절차적 정책 (procedural policy) | procedural policy | 훅 스크립트로 런타임에 검사하는 규칙 |
| 서술적 정책 (descriptive policy) | descriptive policy | AGENTS.md와 슬래시 커맨드로 표현하는 텍스트 지침 |

---

*모듈 2로 이동: [슬래시 커맨드 작성 → 에이전트 작업 명세화](./module-2.md)*

*이 문서는 하니스 엔지니어링 코스 — 모듈 1입니다. 독립적으로 생성 가능하며, 다른 모듈 파일에 의존하지 않습니다.*
