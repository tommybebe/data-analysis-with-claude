# 모듈 4: 오류 처리와 비용 최적화 — 안정적이고 경제적인 에이전트 워크플로 설계

> **학습 시간**: 2~3시간
> **난이도**: 중급~고급
> **핵심 질문**: "에이전트 워크플로가 실패했을 때 어떻게 알아차리고, 얼마를 썼는지 어떻게 알 수 있는가?"

---

## 학습 목표

이 모듈을 완료하면 다음을 할 수 있습니다:

- Claude Code 훅 생애주기(PreToolUse, PostToolUse, Stop)를 사용하여 에이전트 워크플로의 오류를 탐지할 수 있다
- BigQuery 온디맨드 가격 구조를 이해하고 훅으로 쿼리 비용을 사전 제어할 수 있다
- 재시도 가능 오류와 재시도 불가 오류를 분류하고 각각에 맞는 복구 전략을 설계할 수 있다
- `settings.json`에 비용 가드(cost guard) 훅과 재시도 로직을 통합할 수 있다

---

## 사전 조건

### 파일 준비 상태

```
✅ AGENTS.md                                   — 에이전트 컨텍스트 (모듈 1 산출물)
✅ .claude/settings.json                        — 기본 훅 설정 (모듈 2 산출물)
✅ .claude/commands/analyze.md                 — 분석 스킬 (모듈 2 산출물)
✅ .github/workflows/auto-analyze.yml          — 자동 워크플로 (모듈 3 산출물)
✅ GitHub Secrets                              — GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_TOKEN
```

```bash
# 필수 파일 존재 확인
for f in AGENTS.md \
          .claude/settings.json \
          .claude/commands/analyze.md \
          .github/workflows/auto-analyze.yml; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ $f — 없음 (이전 모듈 완료 필요)"
done
```

### 사전 지식

| 영역 | 이 모듈에서 필요한 수준 | 부족하다면 |
|------|----------------------|------------|
| Bash 종료 코드 | `exit 0`(성공), `exit 1`(실패)의 의미, 조건 분기 | [Bash 종료 코드 가이드](https://tldp.org/LDP/abs/html/exit-codes.html) 참조 |
| BigQuery 온디맨드 가격 | 처리된 바이트 × $6.25/TB 계산 원리 | 아래 "BigQuery 비용 기초" 섹션 |
| Claude Code 훅 생애주기 | PreToolUse, PostToolUse, Stop 훅의 실행 시점 | 모듈 2 훅 섹션 복습 |
| HTTP 상태 코드 | 429(요청 초과), 500(서버 오류)의 의미 | 기초 HTTP 개념 자료 |

### BigQuery 비용 기초

**온디맨드(on-demand) 가격** 방식:
- 청구 단위: 쿼리가 **실제로 처리한 바이트 수**
- 단가: **$6.25 / TB** (아시아-동북1 리전 포함 대부분 리전)
- 최소 청구: 쿼리당 **10 MB**

```
비용 계산 예시:
  쿼리 처리량  50 GB  →  50 × $6.25 / 1,000 = $0.3125
  쿼리 처리량   1 GB  →   1 × $6.25 / 1,000 = $0.00625
  쿼리 처리량 200 MB  →               0.2 TB = $0.00125 (최소 단위보다 큼)
  쿼리 처리량  10 MB  →              최소 청구 = $0.000063
```

에이전트가 실수로 전체 테이블 풀 스캔(full scan)을 반복 실행하면 의도치 않은 비용이 발생합니다. 이것이 바로 **비용 가드(cost guard)** 훅이 필요한 이유입니다.

---

## 핵심 개념

### 오류와 비용은 왜 함께 다루어야 하는가

에이전트 워크플로에서 오류 처리와 비용 제어는 분리하기 어렵습니다. 오류가 비용을 만들고, 비용 이상이 오류를 가리키기 때문입니다.

**오류가 비용을 만드는 세 가지 패턴:**

```
패턴 1: 재시도 폭증(retry storm)
  에이전트가 실패 원인 분석 없이 같은 쿼리를 반복 실행
  DAU 집계 쿼리 200 MB × 4회 재시도 → $0.005 (소액이지만 누적 증폭)

패턴 2: 조용한 실패(silent failure) 후 빈 결과 재분석
  빈 결과셋을 "데이터가 없다"고 판단, 다양한 변형 쿼리로 탐색
  각 탐색 쿼리가 전체 테이블 스캔 → 비용 급증

패턴 3: dry-run 없는 대용량 쿼리 직접 실행
  파티션 필터 없는 쿼리가 1 TB 이상 처리 → $6.25+ 단발 청구
```

**비용 이상이 오류를 탐지하는 역방향 신호:**
```
정상 DAU 집계 쿼리: 파티션 7일치 스캔 → ~2 GB → ~$0.013
이상 탐지 기준:
  처리량 > 20 GB  →  파티션 필터 누락 가능성
  처리량 > 50 GB  →  전체 테이블 풀 스캔 강력 의심 → 즉시 중단
```

### 오류 탐지 계층 구조

오류 탐지는 세 개의 계층에서 중첩적으로 이루어져야 합니다:

```
계층 1: 도구 실행 수준 (Tool Execution Level)
  → PreToolUse / PostToolUse 훅에서 탐지
  → BigQuery 쿼리 비용, dbt 테스트 결과, 파일 덮어쓰기 시도

계층 2: 작업 완료 수준 (Task Completion Level)
  → Stop 훅에서 탐지
  → 완료 증거(evidence) 파일 존재, 필수 산출물 생성 여부

계층 3: 워크플로 수준 (Workflow Level)
  → GitHub Actions 단계 성공/실패, 이슈 라벨 상태
  → 단계 간 의존성, 타임아웃, 비용 누적 한도
```

> **하니스 vs 파이프라인 산출물 구분**: 이 모듈에서 작성하는 오류 처리 훅 스크립트(`.claude/hooks/*.sh`)와 `settings.json` 설정은 **하니스(harness) 설정**입니다. 반면 훅이 검증하는 `evidence/` 폴더의 파일들은 **파이프라인 산출물**입니다.

---

## 1단계: 관찰

> **이 단계의 목표**: 완성된 오류 처리 훅과 비용 가드 코드를 읽고, 각 구성요소가 무엇을 하는지 설명할 수 있게 된다.

아직 자신의 훅을 작성하기 전에, **완성된 예시**를 먼저 꼼꼼히 읽습니다. 이 단계에서는 아무것도 수정하지 않습니다.

### 관찰 자료 1: 비용 가드 훅 — `pre_bq_cost_check.sh`

이 스크립트는 `settings.json`의 `PreToolUse` 훅으로 등록되어, 에이전트가 `bq query`를 실행하기 **전에** 자동으로 호출됩니다.

```bash
#!/bin/bash
# .claude/hooks/pre_bq_cost_check.sh
# 역할: BigQuery 쿼리 실행 전 예상 비용 검사 (하니스 PreToolUse 훅)
# 트리거: 에이전트가 bq query 또는 bq --dry_run 명령 실행 시도 시
# 반환:
#   exit 0 → 쿼리 허용
#   exit 1 → 쿼리 차단 (에이전트에게 오류 메시지 전달)
#
# 비용 임계값 (환경 변수로 재정의 가능):
#   BQ_COST_WARN_GB  — 이 값 초과 시 경고 (기본: 10 GB)
#   BQ_COST_BLOCK_GB — 이 값 초과 시 차단 (기본: 50 GB)

set -euo pipefail  # 오류 즉시 종료, 정의되지 않은 변수 오류, 파이프 오류 전파

# 임계값 설정 (환경 변수 없으면 기본값 사용)
WARN_GB="${BQ_COST_WARN_GB:-10}"      # 경고 임계값: 10 GB
BLOCK_GB="${BQ_COST_BLOCK_GB:-50}"    # 차단 임계값: 50 GB

# ── 입력 파싱 ──────────────────────────────────────────────────────────────
# Claude Code는 훅 스크립트에 JSON 형태의 도구 호출 정보를 stdin으로 전달함
# 이미 dry_run인 경우는 그냥 통과 (비용 발생 없음)
TOOL_INPUT=$(cat)  # stdin 전체 읽기

# dry_run 플래그가 이미 있으면 통과 (비용 없음)
if echo "$TOOL_INPUT" | grep -q '"--dry_run"'; then
  echo "✅ dry_run 쿼리 — 비용 없음, 통과"
  exit 0
fi

# 실제 쿼리 추출 (JSON에서 쿼리 문자열 파싱)
QUERY=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# command 또는 query 필드에서 BQ 쿼리 추출
cmd = data.get('command', '') or data.get('query', '')
print(cmd)
" 2>/dev/null || echo "")

if [ -z "$QUERY" ]; then
  echo "⚠️  쿼리 파싱 실패 — 안전을 위해 통과 허용"
  exit 0
fi

# ── dry_run으로 예상 처리량 계산 ──────────────────────────────────────────
# 실제 쿼리를 dry_run으로 실행하여 처리 바이트 수 예측
DRY_RUN_OUTPUT=$(bq query \
  --dry_run \
  --use_legacy_sql=false \
  --format=json \
  "$QUERY" 2>&1 || echo '{"status": "error"}')

# dry_run 실패 시 경고 후 통과 (쿼리 자체 문법 오류는 실행 시 잡힘)
if echo "$DRY_RUN_OUTPUT" | grep -q '"status": "error"'; then
  echo "⚠️  dry_run 실행 실패 — 쿼리 문법 확인 필요"
  exit 0
fi

# 처리 바이트 수 추출 및 GB 변환
BYTES=$(echo "$DRY_RUN_OUTPUT" | python3 -c "
import sys, json, re
output = sys.stdin.read()
# 'Query will process X bytes' 패턴에서 바이트 수 추출
match = re.search(r'(\d+) bytes', output)
print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

BYTES_GB=$(echo "scale=2; $BYTES / 1073741824" | bc)  # 바이트 → GB 변환

# 비용 계산: $6.25 / TB = $0.00625 / GB
COST_USD=$(echo "scale=6; $BYTES_GB * 0.00625" | bc)

echo "📊 예상 쿼리 처리량: ${BYTES_GB} GB → 예상 비용: \$${COST_USD}"

# ── 임계값 비교 및 차단 ────────────────────────────────────────────────────
# GB를 정수로 변환하여 비교 (소수점 비교는 bash에서 복잡하므로 python 사용)
DECISION=$(python3 -c "
bytes_gb = $BYTES_GB
warn = $WARN_GB
block = $BLOCK_GB
if bytes_gb > block:
    print('BLOCK')
elif bytes_gb > warn:
    print('WARN')
else:
    print('OK')
")

case "$DECISION" in
  BLOCK)
    echo "❌ 쿼리 차단: 예상 처리량 ${BYTES_GB} GB가 차단 임계값 ${BLOCK_GB} GB를 초과합니다." >&2
    echo "   원인 후보: 파티션 필터 누락, 전체 테이블 풀 스캔, 날짜 범위 과다" >&2
    echo "   조치: WHERE절에 파티션 필터(날짜 컬럼)를 추가하세요." >&2
    exit 1  # 에이전트에게 오류 신호 → 에이전트가 쿼리 수정 시도
    ;;
  WARN)
    echo "⚠️  경고: 예상 처리량 ${BYTES_GB} GB가 경고 임계값 ${WARN_GB} GB를 초과합니다." >&2
    echo "   비용: \$${COST_USD} — 의도적이라면 계속 진행하세요." >&2
    exit 0  # 경고만 출력, 쿼리는 허용
    ;;
  OK)
    echo "✅ 비용 검사 통과: ${BYTES_GB} GB, \$${COST_USD}"
    exit 0
    ;;
esac
```

### 관찰 자료 2: 완료 증거 검증 훅 — `post_verify_evidence.sh`

이 스크립트는 `settings.json`의 `Stop` 훅으로 등록되어, 에이전트가 작업을 **완료하고 종료할 때** 자동으로 호출됩니다.

```bash
#!/bin/bash
# .claude/hooks/post_verify_evidence.sh
# 역할: 에이전트 종료 시 필수 산출물 파일의 존재와 유효성 검증 (Stop 훅)
# 트리거: 에이전트가 Stop 도구를 호출할 때 (작업 완료 선언 시)
# 반환:
#   exit 0 → 완료 허용
#   exit 1 → 완료 거부 (에이전트가 누락된 산출물 생성 재시도)
#
# 검증 대상: $EVIDENCE_DIR 환경 변수로 지정 (기본: evidence/)

EVIDENCE_DIR="${EVIDENCE_DIR:-evidence}"  # 산출물 디렉토리

# 현재 실행 중인 단계 감지 (라벨 기반)
# CURRENT_STAGE 환경 변수가 없으면 디렉토리 내용으로 추론
CURRENT_STAGE="${CURRENT_STAGE:-unknown}"

echo "🔍 산출물 검증 시작 (단계: $CURRENT_STAGE)"

# ── 공통 검증: evidence/ 디렉토리 존재 ───────────────────────────────────
if [ ! -d "$EVIDENCE_DIR" ]; then
  echo "❌ 산출물 디렉토리 없음: $EVIDENCE_DIR" >&2
  echo "   에이전트가 evidence/ 디렉토리를 생성하지 않았습니다." >&2
  exit 1
fi

# ── 단계별 산출물 검증 ────────────────────────────────────────────────────
check_file_exists_and_nonempty() {
  local file_path="$1"
  local description="$2"
  local min_bytes="${3:-100}"  # 최소 파일 크기 (기본: 100 바이트)

  if [ ! -f "$file_path" ]; then
    echo "❌ 필수 파일 없음: $file_path ($description)" >&2
    return 1
  fi

  local size
  size=$(wc -c < "$file_path")
  if [ "$size" -lt "$min_bytes" ]; then
    echo "❌ 파일 크기 미달: $file_path (${size}B, 최소 ${min_bytes}B 필요)" >&2
    echo "   빈 파일이거나 내용이 너무 적습니다." >&2
    return 1
  fi

  echo "✅ $description: $file_path (${size}B)"
  return 0
}

VALIDATION_FAILED=0  # 검증 실패 플래그

# 단계에 따라 다른 산출물 검증
case "$CURRENT_STAGE" in
  "stage:1-problem")
    check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/problem_statement.md" "문제 정의 문서" 200 || VALIDATION_FAILED=1
    ;;

  "stage:2-deliverables")
    check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/deliverables.md" "산출물 목록 (Markdown)" 100 || VALIDATION_FAILED=1
    check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/deliverables.json" "산출물 목록 (JSON)" 50 || VALIDATION_FAILED=1
    # JSON 유효성 추가 검증
    if [ -f "$EVIDENCE_DIR/deliverables.json" ]; then
      python3 -c "import json; json.load(open('$EVIDENCE_DIR/deliverables.json'))" 2>/dev/null || {
        echo "❌ deliverables.json이 유효한 JSON이 아닙니다" >&2
        VALIDATION_FAILED=1
      }
    fi
    ;;

  "stage:3-spec")
    check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/analysis_spec.md" "분석 스펙 문서" 300 || VALIDATION_FAILED=1
    ;;

  "stage:5-analyze")
    # 이슈 번호로 노트북 파일 검색 (환경 변수 없으면 패턴 매칭)
    NOTEBOOK=$(find notebooks/ -name "analysis_*.py" -newer "$EVIDENCE_DIR" 2>/dev/null | head -1)
    if [ -z "$NOTEBOOK" ]; then
      echo "❌ marimo 노트북(.py) 없음 — notebooks/ 디렉토리 확인" >&2
      VALIDATION_FAILED=1
    else
      echo "✅ marimo 노트북: $NOTEBOOK"
    fi
    ;;

  *)
    # 알 수 없는 단계 — 경고만 출력, 통과
    echo "⚠️  알 수 없는 단계: $CURRENT_STAGE — 공통 검증만 수행"
    ;;
esac

# ── 최종 결과 ─────────────────────────────────────────────────────────────
if [ "$VALIDATION_FAILED" -eq 1 ]; then
  echo "" >&2
  echo "❌ 산출물 검증 실패 — 에이전트가 누락된 파일을 생성해야 합니다." >&2
  exit 1
fi

echo "✅ 모든 산출물 검증 통과"
exit 0
```

### 관찰 자료 3: `settings.json` — 훅 통합 설정

두 훅을 `settings.json`에 등록하는 완성된 설정입니다:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre_bq_cost_check.sh",
            "description": "BigQuery 쿼리 실행 전 예상 비용 검사"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_log_tool_use.sh",
            "description": "도구 실행 결과 로깅 (비용 추적용)"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_verify_evidence.sh",
            "description": "에이전트 종료 시 필수 산출물 검증"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "mcp__bash__run_command(bq query *)",
      "mcp__bash__run_command(bq --dry_run *)",
      "mcp__bash__run_command(dbt run *)",
      "mcp__bash__run_command(dbt test *)",
      "mcp__bash__run_command(git add evidence/*)",
      "mcp__bash__run_command(git add notebooks/*)",
      "mcp__bash__run_command(git commit -m *)",
      "mcp__bash__run_command(git push)"
    ],
    "deny": [
      "mcp__bash__run_command(rm -rf *)",
      "mcp__bash__run_command(git push --force *)",
      "mcp__bash__run_command(bq rm *)"
    ]
  }
}
```

### 관찰 질문 (스스로 생각하기)

1. `pre_bq_cost_check.sh`에서 `exit 1`을 반환하면 에이전트는 어떻게 행동할까?
2. `post_verify_evidence.sh`에서 `Stop` 훅이 `exit 1`을 반환하면, 에이전트는 계속 실행될까 종료될까?
3. `PreToolUse` 훅에서 dry_run 쿼리는 왜 즉시 통과시키는가?
4. `CURRENT_STAGE` 환경 변수를 어떻게 설정하면 단계별 검증이 작동할까?

### 1단계 자기 점검

- [ ] `PreToolUse` 훅이 실행되는 시점 (에이전트의 도구 호출 전/후)을 설명할 수 있다
- [ ] `Stop` 훅이 `exit 1`을 반환했을 때 에이전트가 어떻게 반응하는지 설명할 수 있다
- [ ] `pre_bq_cost_check.sh`에서 차단(BLOCK)과 경고(WARN)의 차이를 설명할 수 있다
- [ ] `settings.json`의 `matcher` 필드가 어떤 역할을 하는지 설명할 수 있다

---

## 2단계: 수정

> **이 단계의 목표**: 불완전하거나 잘못된 훅 설정을 주어진 명세에 맞게 수정하고, 그 이유를 설명할 수 있게 된다.

### 수정 실습 A: 비용 임계값 조정

현재 `pre_bq_cost_check.sh`의 경고 임계값(`WARN_GB=10`)이 FitTrack 합성 데이터셋에 비해 너무 낮습니다. 전체 이벤트 테이블(약 30 GB)을 파티션 필터 없이 스캔하는 것은 막아야 하지만, 정상적인 분석 쿼리(7일치 ~2 GB)는 경고 없이 통과해야 합니다.

**현재 설정:**

```bash
WARN_GB="${BQ_COST_WARN_GB:-10}"   # 경고 임계값: 10 GB
BLOCK_GB="${BQ_COST_BLOCK_GB:-50}" # 차단 임계값: 50 GB
```

**요구사항:**
- 경고 임계값: 정상 쿼리 최대값(2 GB)의 5배인 10 GB (현재와 동일, 유지)
- 차단 임계값: 전체 테이블 크기(30 GB)보다 약간 높은 **40 GB**로 조정
- `settings.json`에서 환경 변수로 프로젝트별 재정의 가능하도록 설정

**수정 후 `settings.json` 관련 부분:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "BQ_COST_WARN_GB=10 BQ_COST_BLOCK_GB=40 bash .claude/hooks/pre_bq_cost_check.sh",
            "description": "BigQuery 쿼리 실행 전 예상 비용 검사 (경고: 10GB, 차단: 40GB)"
          }
        ]
      }
    ]
  }
}
```

> **수정 포인트 해설**: `command` 필드에서 환경 변수를 인라인으로 설정하면 `settings.json`만 수정하여 임계값을 조정할 수 있습니다. 스크립트 파일을 건드리지 않아도 됩니다. 프로젝트마다 테이블 크기가 다르므로 이 방식이 유연합니다.

### 수정 실습 B: 재시도 로직 추가

현재 `post_verify_evidence.sh`는 산출물이 없으면 `exit 1`만 반환합니다. 에이전트에게 어떻게 수정하라는 구체적인 힌트를 추가해야 합니다.

**현재 코드 (실패 메시지만 있음):**

```bash
  "stage:1-problem")
    check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/problem_statement.md" "문제 정의 문서" 200 || VALIDATION_FAILED=1
    ;;
```

**수정 후 코드 (구체적인 재시도 힌트 추가):**

```bash
  "stage:1-problem")
    if ! check_file_exists_and_nonempty \
      "$EVIDENCE_DIR/problem_statement.md" "문제 정의 문서" 200; then
      VALIDATION_FAILED=1
      # 에이전트에게 구체적인 수정 방법을 hint로 제공
      # 이 메시지는 에이전트의 다음 턴 컨텍스트에 포함됨
      echo "💡 재시도 힌트:" >&2
      echo "   다음 내용을 포함하는 evidence/problem_statement.md를 생성하세요:" >&2
      echo "   - 분석 목적 (1~2문장)" >&2
      echo "   - 핵심 분석 질문 (불릿 리스트)" >&2
      echo "   - 성공 기준 (측정 가능한 형태)" >&2
      echo "   - 분석 범위 (포함/제외 항목)" >&2
    fi
    ;;
```

> **수정 포인트 해설**: `exit 1`의 오류 메시지가 구체적일수록 에이전트의 재시도 품질이 높아집니다. 단순히 "파일 없음"보다 "이런 내용을 포함한 파일을 만들어라"는 힌트가 에이전트에게 더 유용합니다.

### 수정 실습 C: 비용 로그 훅 추가

현재 훅 설정에는 `PostToolUse` 훅 스크립트 파일이 없습니다. BigQuery 쿼리 결과의 처리량을 로그 파일에 기록하는 `post_log_tool_use.sh`를 작성하세요.

**요구사항:**
- BigQuery 쿼리 실행 후 처리 바이트와 예상 비용을 `logs/bq_cost.log`에 append
- 로그 형식: `TIMESTAMP | BYTES_GB GB | $COST | QUERY_PREVIEW` (한 줄)
- BQ 명령이 아닌 경우 아무것도 하지 않음

**작성할 코드 (`post_log_tool_use.sh`):**

```bash
#!/bin/bash
# .claude/hooks/post_log_tool_use.sh
# 역할: 도구 실행 결과에서 BigQuery 비용 정보 추출 및 로깅 (PostToolUse 훅)
# 트리거: 에이전트가 bash 명령 실행 완료 시
# 로그 파일: logs/bq_cost.log (없으면 자동 생성)

LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/bq_cost.log"

# ── 입력 파싱 ──────────────────────────────────────────────────────────────
TOOL_OUTPUT=$(cat)  # stdin: 도구 실행 결과 JSON

# BQ 명령 실행 결과인지 확인
IS_BQ=$(echo "$TOOL_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
cmd = data.get('command', '')
print('yes' if 'bq' in cmd else 'no')
" 2>/dev/null || echo "no")

# BQ 명령이 아니면 즉시 종료 (로깅 불필요)
if [ "$IS_BQ" != "yes" ]; then
  exit 0
fi

# ── 비용 정보 추출 ────────────────────────────────────────────────────────
BYTES=$(echo "$TOOL_OUTPUT" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
output = data.get('output', '')
# 'bytes processed: N' 또는 'Statistics: N bytes processed' 패턴 매칭
match = re.search(r'(\d+) bytes processed', output, re.IGNORECASE)
if not match:
    match = re.search(r'bytes_processed[:\s]+(\d+)', output, re.IGNORECASE)
print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

# 쿼리 미리보기 (첫 50자)
QUERY_PREVIEW=$(echo "$TOOL_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
cmd = data.get('command', 'unknown')[:50]
print(cmd.replace('\n', ' '))
" 2>/dev/null || echo "unknown")

# GB 변환 및 비용 계산
BYTES_GB=$(echo "scale=4; $BYTES / 1073741824" | bc)
COST_USD=$(echo "scale=6; $BYTES_GB * 0.00625" | bc)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── 로그 파일에 기록 ──────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"  # 디렉토리 없으면 생성
echo "${TIMESTAMP} | ${BYTES_GB} GB | \$${COST_USD} | ${QUERY_PREVIEW}" >> "$LOG_FILE"

echo "📝 비용 로그 기록: ${BYTES_GB} GB, \$${COST_USD}"
exit 0
```

### 수정 실습 D: `settings.json` 오류 수정

아래 `settings.json`에는 두 가지 오류가 있습니다. 찾아서 수정하세요.

**버그가 있는 설정:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "script",
            "command": "bash .claude/hooks/pre_bq_cost_check.sh"
          }
        ]
      }
    ],
    "Stop": {
      "hooks": [
        {
          "type": "command",
          "command": "bash .claude/hooks/post_verify_evidence.sh"
        }
      ]
    }
  }
}
```

**버그 설명:**
1. `PreToolUse` 훅의 `type` 값이 `"script"`인데, 올바른 값은 `"command"`입니다
2. `Stop` 훅의 구조가 잘못되었습니다 — `hooks` 배열이 최상위 배열 안에 있어야 합니다

**수정 후 설정:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre_bq_cost_check.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_verify_evidence.sh"
          }
        ]
      }
    ]
  }
}
```

### 2단계 자기 점검

- [ ] `BQ_COST_BLOCK_GB=40`으로 설정해야 하는 이유를 FitTrack 데이터셋 크기와 연결하여 설명할 수 있다
- [ ] 훅의 오류 메시지에 재시도 힌트를 추가하는 것이 왜 에이전트 행동에 영향을 미치는지 설명할 수 있다
- [ ] `PostToolUse` 훅과 `Stop` 훅의 실행 시점 차이를 설명할 수 있다
- [ ] `settings.json`의 훅 `type`이 `"command"`여야 하는 이유를 설명할 수 있다

---

## 3단계: 창작

> **이 단계의 목표**: 프로젝트에 맞는 완전한 오류 처리와 비용 모니터링 시스템을 처음부터 설계하고 구현한다.

관찰과 수정으로 쌓인 이해를 바탕으로, 이제 **완전한 오류 처리 + 비용 최적화 시스템**을 직접 구현합니다.

### 창작 실습 1: 재시도 가능 여부 분류기 작성

에이전트 워크플로에서 발생하는 오류는 재시도 가능 여부에 따라 다르게 처리해야 합니다. 두 가지 범주를 명확히 분류하는 스크립트를 작성합니다.

**재시도 가능 오류 (일시적, 자동 재시도 적합):**
- HTTP 429 (API 요청 초과) — 잠시 후 재시도
- HTTP 500 (서버 일시 오류) — 짧은 지연 후 재시도
- BigQuery "Backend error" — 1~2회 재시도

**재시도 불가 오류 (구조적, 사람 개입 필요):**
- HTTP 401/403 (인증 실패) — 토큰 갱신 필요
- BigQuery "Table not found" — dbt 모델 미빌드 또는 오타
- BigQuery "Quota exceeded" (일별 한도) — 다음 날까지 대기
- 빈 결과셋 (0 rows) — 날짜 범위 또는 쿼리 로직 오류

```bash
#!/bin/bash
# .claude/hooks/classify_error.sh
# 역할: 오류 메시지를 분석하여 재시도 가능 여부 분류
# 반환:
#   exit 0 + "RETRYABLE"   → 자동 재시도 허용
#   exit 0 + "ESCALATE"    → 사람 개입 필요, 재시도 금지
#   exit 0 + "UNKNOWN"     → 분류 불가, 보수적으로 에스컬레이션
# 사용법: echo "오류 메시지" | bash classify_error.sh

ERROR_MSG=$(cat)  # stdin에서 오류 메시지 읽기

# ── 재시도 가능 패턴 ──────────────────────────────────────────────────────
RETRYABLE_PATTERNS=(
  "429"                          # HTTP 429 Too Many Requests
  "Rate limit"                   # API 요청 속도 제한
  "Backend error"                # BigQuery 일시적 백엔드 오류
  "Connection timed out"         # 네트워크 타임아웃
  "Service Unavailable"          # HTTP 503
  "Quota exceeded.*per minute"   # 분당 쿼터 초과 (일별 아님)
)

# ── 재시도 불가 패턴 ──────────────────────────────────────────────────────
ESCALATE_PATTERNS=(
  "401"                          # 인증 실패
  "403"                          # 권한 없음
  "Table not found"              # 테이블 존재하지 않음 (dbt 미실행)
  "View not found"               # 뷰 존재하지 않음
  "Dataset not found"            # 데이터셋 존재하지 않음
  "Daily quota exceeded"         # 일별 쿼터 초과 (당일 재시도 무의미)
  "Access Denied"                # 접근 권한 없음 (IAM 설정 문제)
  "Authentication"               # 인증 관련 모든 오류
  "invalid_grant"                # OAuth 토큰 만료
)

# 재시도 가능 패턴 검사
for pattern in "${RETRYABLE_PATTERNS[@]}"; do
  if echo "$ERROR_MSG" | grep -qi "$pattern"; then
    echo "RETRYABLE"
    echo "🔄 재시도 가능 오류 탐지: $pattern 패턴" >&2
    exit 0
  fi
done

# 재시도 불가 패턴 검사
for pattern in "${ESCALATE_PATTERNS[@]}"; do
  if echo "$ERROR_MSG" | grep -qi "$pattern"; then
    echo "ESCALATE"
    echo "🆘 에스컬레이션 필요 오류 탐지: $pattern 패턴" >&2
    echo "   사람이 원인을 분석하고 수동으로 수정해야 합니다." >&2
    exit 0
  fi
done

# 분류 불가 → 보수적으로 에스컬레이션
echo "UNKNOWN"
echo "⚠️  오류 패턴 분류 불가 — 보수적으로 에스컬레이션 처리" >&2
exit 0
```

### 창작 실습 2: 지수 백오프 재시도 래퍼

재시도 가능 오류에 대해 지수 백오프(exponential backoff)를 적용하는 래퍼 스크립트를 작성합니다. 재시도 폭증(retry storm)을 방지합니다.

```bash
#!/bin/bash
# .claude/hooks/retry_with_backoff.sh
# 역할: 명령을 지수 백오프 방식으로 최대 N회 재시도
# 사용법: bash retry_with_backoff.sh "실행할 명령"
# 환경 변수:
#   MAX_RETRIES     — 최대 재시도 횟수 (기본: 3)
#   INITIAL_WAIT    — 첫 재시도 대기 시간(초) (기본: 5)
#   BACKOFF_FACTOR  — 대기 시간 증가 배수 (기본: 2)
#
# 비용 참고: 재시도 시 BigQuery 쿼리가 재실행됩니다.
# MAX_RETRIES=3, 쿼리당 200 MB라면 최대 총 800 MB → ~$0.005

MAX_RETRIES="${MAX_RETRIES:-3}"         # 최대 3회 재시도
INITIAL_WAIT="${INITIAL_WAIT:-5}"       # 첫 대기: 5초
BACKOFF_FACTOR="${BACKOFF_FACTOR:-2}"   # 매 재시도마다 2배 증가

COMMAND="$1"  # 실행할 명령

if [ -z "$COMMAND" ]; then
  echo "❌ 오류: 실행할 명령을 첫 번째 인자로 전달하세요" >&2
  exit 1
fi

# 재시도 루프
attempt=1
wait_time=$INITIAL_WAIT

while [ "$attempt" -le "$MAX_RETRIES" ]; do
  echo "🔄 시도 $attempt/$MAX_RETRIES: $COMMAND"

  # 명령 실행 및 결과 캡처
  OUTPUT=$(eval "$COMMAND" 2>&1)
  EXIT_CODE=$?

  if [ "$EXIT_CODE" -eq 0 ]; then
    # 성공
    echo "✅ 성공 (시도 $attempt/$MAX_RETRIES)"
    echo "$OUTPUT"
    exit 0
  fi

  # 실패 — 재시도 가능 여부 분류
  DECISION=$(echo "$OUTPUT" | bash .claude/hooks/classify_error.sh)

  if [ "$DECISION" = "ESCALATE" ] || [ "$DECISION" = "UNKNOWN" ]; then
    echo "🆘 재시도 불가 오류 — 즉시 에스컬레이션" >&2
    echo "$OUTPUT" >&2
    exit 1
  fi

  if [ "$attempt" -lt "$MAX_RETRIES" ]; then
    echo "⏳ ${wait_time}초 대기 후 재시도..." >&2
    sleep "$wait_time"
    wait_time=$(echo "$wait_time * $BACKOFF_FACTOR" | bc | cut -d. -f1)  # 정수 변환
  fi

  attempt=$((attempt + 1))
done

# 최대 재시도 횟수 초과
echo "❌ 최대 재시도 횟수($MAX_RETRIES) 초과 — 에스컬레이션" >&2
exit 1
```

### 창작 실습 3: 비용 일일 리포트 생성기

`logs/bq_cost.log`를 파싱하여 일일 비용 요약을 생성하는 Python 스크립트를 작성합니다.

```python
#!/usr/bin/env python3
# scripts/daily_cost_report.py
# 역할: bq_cost.log를 파싱하여 일일 BigQuery 비용 요약 생성
# 사용법: python3 scripts/daily_cost_report.py [--date YYYY-MM-DD]
# 출력: 콘솔 요약 + reports/cost_YYYY-MM-DD.md 파일
#
# 비용 예시 (FitTrack 일반 분석 기준):
#   이슈 1건당 예상 총 비용: ~$0.05~0.15 (분석 복잡도에 따라)
#   월 10건 분석 시 예상: ~$0.50~1.50

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

def parse_cost_log(log_file: Path, target_date: str) -> list[dict]:
    """
    bq_cost.log 파일을 파싱하여 특정 날짜의 쿼리 비용 목록 반환.

    로그 형식:
    TIMESTAMP | BYTES_GB GB | $COST | QUERY_PREVIEW
    예: 2026-03-22T10:30:00Z | 1.2345 GB | $0.007716 | SELECT * FROM fct_daily...
    """
    entries = []

    if not log_file.exists():
        print(f"⚠️  로그 파일 없음: {log_file}")
        return entries

    # 로그 파싱 정규식
    pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2})T[\d:Z]+ \| ([\d.]+) GB \| \$([\d.]+) \| (.+)'
    )

    with log_file.open('r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                print(f"⚠️  파싱 실패 (줄 {line_no}): {line[:60]}...")
                continue

            date, bytes_gb, cost_usd, query_preview = match.groups()

            # 날짜 필터링
            if date != target_date:
                continue

            entries.append({
                'date': date,
                'bytes_gb': float(bytes_gb),
                'cost_usd': float(cost_usd),
                'query_preview': query_preview[:80],  # 최대 80자
            })

    return entries


def generate_report(entries: list[dict], target_date: str) -> str:
    """
    쿼리 목록을 받아 Markdown 형식의 일일 비용 리포트 생성.
    """
    total_gb = sum(e['bytes_gb'] for e in entries)
    total_cost = sum(e['cost_usd'] for e in entries)
    query_count = len(entries)

    # 상위 3개 비싼 쿼리
    top_queries = sorted(entries, key=lambda x: x['cost_usd'], reverse=True)[:3]

    # BigQuery 온디맨드 기준 비용 경고 수준 분류
    if total_cost < 0.10:
        cost_level = "🟢 정상"
    elif total_cost < 0.50:
        cost_level = "🟡 주의"
    else:
        cost_level = "🔴 검토 필요"

    lines = [
        f"# BigQuery 일일 비용 리포트 — {target_date}",
        "",
        "## 요약",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 날짜 | {target_date} |",
        f"| 총 쿼리 수 | {query_count}회 |",
        f"| 총 처리량 | {total_gb:.2f} GB |",
        f"| 총 비용 | ${total_cost:.6f} |",
        f"| 비용 수준 | {cost_level} |",
        "",
        "> **참고**: BigQuery 온디맨드 단가 $6.25/TB 기준",
        "",
    ]

    if top_queries:
        lines += [
            "## 상위 비용 쿼리 (최대 3개)",
            "",
            "| 비용 | 처리량 | 쿼리 미리보기 |",
            "|------|--------|--------------|",
        ]
        for q in top_queries:
            lines.append(
                f"| ${q['cost_usd']:.6f} | {q['bytes_gb']:.2f} GB | `{q['query_preview']}` |"
            )
        lines.append("")

    if not entries:
        lines += [
            "## 데이터 없음",
            "",
            f"{target_date} 날짜의 BigQuery 쿼리 기록이 없습니다.",
        ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="BigQuery 일일 비용 리포트 생성")
    parser.add_argument(
        '--date',
        default=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        help="리포트 날짜 (YYYY-MM-DD 형식, 기본: 오늘)"
    )
    parser.add_argument(
        '--log-file',
        default='logs/bq_cost.log',
        help="비용 로그 파일 경로 (기본: logs/bq_cost.log)"
    )
    args = parser.parse_args()

    log_file = Path(args.log_file)
    entries = parse_cost_log(log_file, args.date)

    report_text = generate_report(entries, args.date)

    # 콘솔 출력
    print(report_text)

    # 파일 저장
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"cost_{args.date}.md"
    report_file.write_text(report_text, encoding='utf-8')
    print(f"\n✅ 리포트 저장: {report_file}")


if __name__ == "__main__":
    main()
```

### 창작 실습 4: 최종 통합 — `settings.json` 완성

지금까지 만든 모든 훅을 통합한 완전한 `settings.json`을 작성합니다:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "BQ_COST_WARN_GB=10 BQ_COST_BLOCK_GB=40 bash .claude/hooks/pre_bq_cost_check.sh",
            "description": "BigQuery 쿼리 실행 전 예상 비용 검사 (경고: 10GB, 차단: 40GB)"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_log_tool_use.sh",
            "description": "BigQuery 쿼리 비용 로깅"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_verify_evidence.sh",
            "description": "에이전트 종료 시 필수 산출물 검증 — 누락 시 재시도 힌트 제공"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "mcp__bash__run_command(bq query *)",
      "mcp__bash__run_command(bq --dry_run *)",
      "mcp__bash__run_command(dbt run *)",
      "mcp__bash__run_command(dbt test *)",
      "mcp__bash__run_command(dbt compile *)",
      "mcp__bash__run_command(git add evidence/*)",
      "mcp__bash__run_command(git add notebooks/*)",
      "mcp__bash__run_command(git commit -m *)",
      "mcp__bash__run_command(git push)",
      "mcp__bash__run_command(python3 scripts/*.py *)",
      "mcp__bash__run_command(marimo export *)"
    ],
    "deny": [
      "mcp__bash__run_command(rm -rf *)",
      "mcp__bash__run_command(git push --force *)",
      "mcp__bash__run_command(bq rm *)",
      "mcp__bash__run_command(gcloud projects delete *)"
    ]
  }
}
```

### 창작 완료 검증

```bash
# 1. 모든 훅 스크립트 파일 존재 확인
for f in .claude/hooks/pre_bq_cost_check.sh \
          .claude/hooks/post_verify_evidence.sh \
          .claude/hooks/post_log_tool_use.sh \
          .claude/hooks/classify_error.sh \
          .claude/hooks/retry_with_backoff.sh; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ $f — 없음"
done

# 2. 훅 스크립트 실행 권한 확인
for f in .claude/hooks/*.sh; do
  [ -x "$f" ] && echo "✅ 실행 권한: $f" || {
    echo "⚠️  실행 권한 없음: $f — chmod +x $f 실행"
    chmod +x "$f"
  }
done

# 3. settings.json JSON 유효성 검증
python3 -c "
import json
with open('.claude/settings.json') as f:
    data = json.load(f)
hooks = data.get('hooks', {})
required = ['PreToolUse', 'PostToolUse', 'Stop']
for r in required:
    status = '✅' if r in hooks else '❌'
    print(f'{status} {r} 훅 존재')
"

# 4. 비용 가드 훅 단독 테스트 (dry_run 명령 — 통과해야 함)
echo '{"command": "bq query --dry_run SELECT 1"}' | \
  bash .claude/hooks/pre_bq_cost_check.sh && \
  echo "✅ 비용 가드 훅 통과 (dry_run)" || \
  echo "❌ 비용 가드 훅 실패"

# 5. 오류 분류기 테스트
echo "Error 429 Rate limit exceeded" | \
  bash .claude/hooks/classify_error.sh | \
  grep -q "RETRYABLE" && echo "✅ 재시도 가능 오류 분류 정상" || echo "❌ 분류 오류"

echo "Table not found: project.dataset.table" | \
  bash .claude/hooks/classify_error.sh | \
  grep -q "ESCALATE" && echo "✅ 에스컬레이션 오류 분류 정상" || echo "❌ 분류 오류"

# 6. 비용 리포트 생성 테스트
mkdir -p logs
echo "$(date -u +%Y-%m-%d)T10:00:00Z | 1.5000 GB | \$0.009375 | SELECT date, count(*) FROM fct_daily" \
  >> logs/bq_cost.log
python3 scripts/daily_cost_report.py && echo "✅ 비용 리포트 생성 정상"
```

---

## 모듈 자기 점검 체크리스트

아래 항목을 직접 검증하세요. **모든 항목이 ✅일 때만 모듈 4를 완료한 것으로 간주합니다.**

### 훅 스크립트 검증

- [ ] **PASS**: `.claude/hooks/pre_bq_cost_check.sh`가 존재하고 실행 권한이 있다
  - **FAIL 기준**: 파일 없음 또는 `ls -l .claude/hooks/pre_bq_cost_check.sh | grep "^-r"` (실행 권한 없음)
  - **FAIL 시 조치**: 창작 실습 (관찰 자료 1)의 코드를 저장하고 `chmod +x` 실행

- [ ] **PASS**: `pre_bq_cost_check.sh`에 WARN/BLOCK 임계값이 FitTrack 데이터셋에 맞게 설정되어 있다
  - **FAIL 기준**: BLOCK_GB가 30 GB 이하로 설정되어 정상 쿼리도 차단됨
  - **검증**: `grep "BLOCK_GB" .claude/hooks/pre_bq_cost_check.sh` → 40 이상이어야 함
  - **FAIL 시 조치**: 수정 실습 A에 따라 임계값 조정

- [ ] **PASS**: `post_verify_evidence.sh`의 각 단계별 검증에 재시도 힌트 메시지가 포함되어 있다
  - **FAIL 기준**: 실패 시 "파일 없음" 외 구체적인 힌트 없음
  - **FAIL 시 조치**: 수정 실습 B의 재시도 힌트 패턴 적용

- [ ] **PASS**: `classify_error.sh`가 재시도 가능/불가 오류를 올바르게 분류한다
  - **검증 명령**: `echo "429 Rate limit" | bash .claude/hooks/classify_error.sh` → `RETRYABLE`
  - **검증 명령**: `echo "Table not found" | bash .claude/hooks/classify_error.sh` → `ESCALATE`
  - **FAIL 기준**: 위 두 테스트 중 하나라도 잘못된 결과
  - **FAIL 시 조치**: 창작 실습 1의 패턴 배열에 해당 패턴 추가

### `settings.json` 검증

- [ ] **PASS**: `settings.json`에 PreToolUse, PostToolUse, Stop 세 가지 훅이 모두 등록되어 있다
  - **검증**: `python3 -c "import json; d=json.load(open('.claude/settings.json')); print(list(d.get('hooks',{}).keys()))"`
  - **FAIL 기준**: 세 훅 중 하나라도 없음
  - **FAIL 시 조치**: 창작 실습 4의 통합 `settings.json` 적용

- [ ] **PASS**: `settings.json`이 유효한 JSON이다
  - **검증**: `python3 -m json.tool .claude/settings.json > /dev/null && echo "유효"`
  - **FAIL 기준**: JSON 파싱 오류
  - **FAIL 시 조치**: 수정 실습 D의 오류 패턴 참조하여 수정

- [ ] **PASS**: `deny` 목록에 `rm -rf`, `git push --force`, `bq rm`이 있다
  - **FAIL 기준**: `grep "deny" .claude/settings.json` 후 위 세 패턴 중 하나라도 없음
  - **FAIL 시 조치**: 창작 실습 4의 deny 목록 참조

### 비용 모니터링 검증

- [ ] **PASS**: `logs/bq_cost.log`에 쿼리 비용 로그가 기록된다
  - **검증 방법**: 에이전트를 실행하거나 수동으로 로그 라인 추가 후 리포트 생성 테스트
  - **FAIL 기준**: 로그 파일 없음 또는 비어 있음
  - **FAIL 시 조치**: 창작 완료 검증 6번 명령 실행 후 `post_log_tool_use.sh` 동작 확인

- [ ] **PASS**: `scripts/daily_cost_report.py`가 오류 없이 실행된다
  - **검증**: `python3 scripts/daily_cost_report.py --date $(date +%Y-%m-%d)`
  - **FAIL 기준**: 스크립트 실행 오류 또는 `reports/` 디렉토리 미생성
  - **FAIL 시 조치**: 창작 실습 3의 코드 저장 후 재실행

### 개념 이해 검증

- [ ] **PASS**: "이 프로젝트에서 한 달에 10개 이슈를 분석하면 BigQuery 비용이 얼마가 예상되는가?"에 수치로 답할 수 있다
  - **예상 답변 범위**: $0.50~$2.00 (정확한 값 불필요, 합리적인 추정)
  - **FAIL 기준**: "모른다" 또는 전혀 계산 불가
  - **FAIL 시 조치**: 핵심 개념의 "BigQuery 비용 기초" 섹션과 비용 계산 예시 다시 읽기

- [ ] **PASS**: "에이전트가 `Table not found` 오류를 만났을 때 재시도하면 안 되는 이유"를 설명할 수 있다
  - **예상 답변**: 테이블이 존재하지 않는 것은 구조적 오류 — 재시도해도 같은 결과, 비용만 증가
  - **FAIL 기준**: 재시도해도 된다고 판단하거나 이유 설명 불가
  - **FAIL 시 조치**: 핵심 개념의 "오류와 비용은 왜 함께 다루어야 하는가" 섹션 재읽기

---

## 통합과 개선 — 하니스의 유지보수

모듈 1~3에서 하니스를 구축하고, 이 모듈 전반부에서 오류 처리와 비용 최적화를 추가했습니다. 하지만 하니스는 **만들면 끝나는 것이 아닙니다**. 시간이 지나면 코드, 문서, 규칙 사이에 불일치가 쌓이고, 에이전트의 행동이 초기 설계에서 벗어나기 시작합니다. 이 섹션에서는 하니스를 장기적으로 건강하게 유지하는 세 가지 축 — **엔트로피 관리**, **점진적 자율성**, **유지보수 루틴** — 을 다룹니다.

---

### 핵심 개념: 하니스 엔트로피

**엔트로피(entropy)** 는 하니스 구성 요소 사이의 불일치, 중복, 노후화가 누적되는 현상입니다. 소프트웨어 엔지니어링에서 "기술 부채"와 유사하지만, 하니스 엔트로피는 에이전트가 생성하는 산출물의 품질에 직접 영향을 미칩니다.

```
하니스 엔트로피의 세 가지 유형:

1. 문서-코드 불일치 (Document-Code Drift)
   AGENTS.md에 "staging 모델을 직접 참조하지 마세요"라고 적혀 있지만,
   실제로 에이전트가 staging 모델을 참조해도 훅이 잡지 못하는 상태

2. 규칙 중복·모순 (Rule Redundancy/Conflict)
   settings.json의 deny 목록에 "bq rm *"이 있고,
   AGENTS.md에도 "BigQuery 테이블을 삭제하지 마세요"가 있지만,
   하나는 업데이트되고 다른 하나는 갱신되지 않아 불일치 발생

3. 산출물 부패 (Artifact Rot)
   3개월 전 만든 marimo 노트북이 현재 dbt 모델 스키마와 맞지 않음,
   evidence/ 디렉토리에 더 이상 사용되지 않는 검증 파일이 방치됨
```

> **하니스 vs 파이프라인 산출물 구분 (복습)**: 엔트로피 관리의 대상은 **하니스 구성 요소**(AGENTS.md, settings.json, 훅 스크립트, 워크플로 YAML)입니다. 파이프라인 산출물(evidence/, notebooks/, reports/)은 파이프라인이 자동으로 재생성하므로, 하니스가 건강하면 산출물도 건강합니다.

---

## 1단계: 관찰 (observe)

> **이 단계의 목표**: 전체 파이프라인을 처음부터 끝까지 실행하고, 하니스 구성 요소 사이에 어떤 엔트로피가 축적되었는지 관찰한다.

이 관찰 단계에서는 아무것도 수정하지 않습니다. 기존 하니스를 "있는 그대로" 실행하고, 문제 신호를 발견하는 데 집중합니다.

### 관찰 활동 1: 전체 파이프라인 종단간 실행

모듈 1~3에서 구축한 하니스와 이 모듈 전반부의 훅을 모두 포함한 상태에서 새로운 분석 이슈를 생성하고, 7단계 워크플로가 끝까지 실행되는지 관찰합니다.

```bash
# 새로운 분석 이슈 생성 (주간 리텐션율 분석)
gh issue create \
  --title "주간 리텐션율 추이 분석 (W1~W4)" \
  --body "FitTrack 앱의 주간 리텐션율(W1, W2, W3, W4)을
2026년 1월~3월 기간 동안 분석해주세요.

- 코호트: 주 단위 신규 가입자 그룹
- 지표: W1(7일), W2(14일), W3(21일), W4(28일) 리텐션율
- 시각화: 코호트별 리텐션 커브 (라인 차트)
- 비교: 월별 코호트 간 리텐션율 차이" \
  --label "auto-analyze"

# 실행 모니터링
gh run watch --exit-status
```

### 관찰 활동 2: 엔트로피 신호 탐지

파이프라인 실행이 완료된 후(성공이든 실패든), 다음 명령으로 엔트로피 신호를 체계적으로 탐지합니다.

**엔트로피 신호 체크리스트:**

| # | 신호 유형 | 탐지 방법 | 엔트로피 의미 |
|---|----------|----------|-------------|
| 1 | 중복된 SQL 로직 | `grep -rn "COUNT(DISTINCT user_id)" models/ notebooks/` | 같은 집계 로직이 dbt 모델과 노트북에 동시 존재 — 하나가 변경되면 불일치 |
| 2 | 문서화되지 않은 데이터 소스 | `diff <(grep -oP "FROM \K[\w.]+" notebooks/*.py \| sort -u) <(grep -oP "name: \K\w+" models/staging/sources.yml \| sort -u)` | 노트북이 sources.yml에 없는 테이블을 직접 참조 |
| 3 | 고아 노트북 | `find notebooks/ -name "*.py" -mtime +30 -exec grep -L "import marimo" {} \;` | 30일 이상 수정되지 않은 비-marimo Python 파일 — 사용 여부 불명 |
| 4 | 부패한 AGENTS.md 규칙 | 아래 스크립트 참조 | AGENTS.md의 규칙이 실제 설정과 일치하지 않음 |
| 5 | 미사용 훅 스크립트 | `for f in .claude/hooks/*.sh; do grep -q "$(basename $f)" .claude/settings.json \|\| echo "미등록: $f"; done` | settings.json에 등록되지 않은 훅 — 작성했지만 활성화하지 않은 것 |
| 6 | 비용 로그 이상 | `tail -20 logs/bq_cost.log \| awk -F'\|' '{sum += $3} END {print sum}'` | 최근 20개 쿼리의 비용 합계가 비정상적으로 높음 |
| 7 | 권한 정책 구멍 | `python3 -c "import json; d=json.load(open('.claude/settings.json')); print(len(d.get('permissions',{}).get('deny',[])))"` | deny 규칙 수가 3개 미만이면 위험 행동 차단 부족 |

**AGENTS.md 불일치 탐지 스크립트:**

```bash
#!/bin/bash
# scripts/detect_agents_drift.sh
# 역할: AGENTS.md의 규칙이 실제 하니스 설정과 일치하는지 검증
# 출력: 불일치 항목 목록

echo "=== AGENTS.md 불일치 탐지 ==="
DRIFT_COUNT=0

# 검사 1: AGENTS.md에 "staging 직접 참조 금지" 규칙이 있는가?
if grep -q "staging.*직접.*참조.*금지\|staging.*직접.*참조하지" AGENTS.md 2>/dev/null; then
  echo "✅ AGENTS.md: staging 직접 참조 금지 규칙 존재"
  # 실제로 훅이 이 규칙을 강제하는지 확인
  if grep -q "staging" .claude/hooks/*.sh 2>/dev/null; then
    echo "   ✅ 훅에서 staging 참조 검사 로직 존재"
  else
    echo "   ⚠️  훅에서 staging 참조를 검사하지 않음 — 규칙만 있고 강제가 없음"
    DRIFT_COUNT=$((DRIFT_COUNT + 1))
  fi
else
  echo "⚠️  AGENTS.md에 staging 참조 제한 규칙 없음"
fi

# 검사 2: AGENTS.md의 비용 한도와 settings.json의 임계값 비교
AGENTS_LIMIT=$(grep -oP '\d+\s*GB' AGENTS.md | head -1 | grep -oP '\d+')
SETTINGS_LIMIT=$(grep -oP 'BQ_COST_BLOCK_GB=\K\d+' .claude/settings.json 2>/dev/null)

if [ -n "$AGENTS_LIMIT" ] && [ -n "$SETTINGS_LIMIT" ]; then
  if [ "$AGENTS_LIMIT" != "$SETTINGS_LIMIT" ]; then
    echo "⚠️  비용 한도 불일치: AGENTS.md=${AGENTS_LIMIT}GB vs settings.json=${SETTINGS_LIMIT}GB"
    DRIFT_COUNT=$((DRIFT_COUNT + 1))
  else
    echo "✅ 비용 한도 일치: ${AGENTS_LIMIT}GB"
  fi
fi

# 검사 3: AGENTS.md에 언급된 파일이 실제로 존재하는지
echo ""
echo "--- AGENTS.md에 언급된 파일 존재 여부 ---"
grep -oP '`[^`]+\.(sh|json|yml|sql|py|md)`' AGENTS.md | tr -d '`' | sort -u | while read filepath; do
  if [ -f "$filepath" ]; then
    echo "  ✅ $filepath"
  else
    echo "  ❌ $filepath — 언급되었지만 존재하지 않음"
    # 서브셸이라 직접 증가시킬 수 없으므로 출력에 표시
  fi
done

echo ""
echo "=== 탐지된 불일치: ${DRIFT_COUNT}건 ==="
```

### 관찰 활동 3: AGENTS.md 규칙 변화 추적 (Before/After)

아래는 AGENTS.md 규칙이 실제 관행에서 벗어난 실제 사례입니다. "관찰" 단계에서는 이런 불일치를 **발견만** 합니다.

**Before — 초기 AGENTS.md 규칙 (모듈 1에서 작성):**

```markdown
## 데이터 접근 규칙

- BigQuery 쿼리 시 반드시 파티션 필터를 포함하세요
- 쿼리당 최대 스캔량: 1 GB
- staging 모델을 직접 참조하지 마세요 — marts 레이어만 사용
```

**After — 3주 후 실제 관행과의 괴리:**

```markdown
## 데이터 접근 규칙  ← 이 규칙은 변경 없음

- BigQuery 쿼리 시 반드시 파티션 필터를 포함하세요  ← 실제: 에이전트가 INFORMATION_SCHEMA 쿼리에서 파티션 필터 없이 실행 (정상적 행동이지만 규칙과 모순)
- 쿼리당 최대 스캔량: 1 GB  ← 실제: 리텐션 분석에서 코호트 조인 시 2.3 GB 스캔 발생 (BLOCK_GB=40이므로 통과했지만 규칙 위반)
- staging 모델을 직접 참조하지 마세요  ← 실제: 에이전트가 디버깅 시 stg_events를 직접 조회 (훅이 차단하지 않아 통과)
```

> **관찰 질문**: 위 세 가지 괴리 중 가장 위험한 것은 무엇이며, 왜 그런가? (2단계에서 수정합니다)

### 관찰 활동 4: 정리 스프린트 준비 — 엔트로피 인벤토리 작성

파이프라인 실행 결과와 탐지 스크립트 출력을 종합하여, 다음 표를 채웁니다. 이 표가 2단계(수정)의 작업 목록이 됩니다.

```markdown
# 엔트로피 인벤토리

| # | 발견 항목 | 유형 | 심각도 | 영향 범위 | 수정 난이도 |
|---|----------|------|--------|----------|-----------|
| 1 | (예: AGENTS.md 비용 한도 vs settings.json 불일치) | 문서-코드 불일치 | 높음 | 비용 정책 | 쉬움 |
| 2 | (예: notebooks/에 고아 파일 3개) | 산출물 부패 | 낮음 | 디스크 정리 | 쉬움 |
| 3 | (예: staging 참조 금지 규칙에 대한 훅 부재) | 규칙 중복·모순 | 중간 | 데이터 품질 | 중간 |
| 4 | | | | | |
| 5 | | | | | |
```

### 1단계 자기 점검

- [ ] 전체 파이프라인을 종단간 실행하여 결과(성공 또는 실패)를 확인했다
- [ ] 엔트로피 신호 체크리스트 7개 항목을 모두 실행하고, 각 결과를 기록했다
- [ ] `detect_agents_drift.sh`를 실행하여 AGENTS.md와 실제 설정 사이의 불일치를 1개 이상 발견했다
- [ ] 엔트로피 인벤토리 표에 3개 이상의 발견 항목을 기록했다
- [ ] 각 발견 항목에 대해 "수정하지 않으면 어떤 문제가 발생하는가?"를 한 문장으로 적을 수 있다

---

## 2단계: 수정 (modify)

> **이 단계의 목표**: 1단계에서 발견한 엔트로피 항목을 수정하고, 하니스 구성 요소를 갱신한다.

### 엔트로피 관리 실습

#### 실습 A: AGENTS.md 규칙 갱신

1단계에서 발견한 AGENTS.md 괴리를 수정합니다. 규칙을 "현실에 맞게" 조정하되, 안전 경계는 유지합니다.

**수정 원칙:**
- 규칙이 너무 엄격하여 정상적 작업을 방해한다면 → 규칙을 완화하되 예외 조건을 명시
- 규칙이 있지만 강제 수단이 없다면 → 훅을 추가하거나, 규칙을 "권장"으로 격하
- 규칙이 중복되어 있다면 → 하나의 권위 있는 위치(single source of truth)로 통합

**수정 예시 — 파티션 필터 규칙 갱신:**

```markdown
## 데이터 접근 규칙 (v2 — 2026-03-22 갱신)

- BigQuery 쿼리 시 **데이터 테이블에 대해** 반드시 파티션 필터를 포함하세요
  - 예외: `INFORMATION_SCHEMA` 쿼리는 파티션 필터 불필요
  - 예외: `--dry_run` 쿼리는 비용이 발생하지 않으므로 필터 불필요
- 쿼리당 최대 스캔량: **5 GB** (이전: 1 GB — 코호트 조인 쿼리의 정상 범위 반영)
  - 경고 임계값: 10 GB (settings.json의 BQ_COST_WARN_GB와 동기화)
  - 차단 임계값: 40 GB (settings.json의 BQ_COST_BLOCK_GB와 동기화)
- staging 모델을 직접 참조하지 마세요 — marts 레이어만 사용
  - **강제 수단**: `pre_bq_cost_check.sh`에 staging 테이블명 패턴 검사 추가 예정 (TODO)
```

> **수정 포인트**: 규칙마다 "강제 수단"을 명시합니다. 강제 수단이 없는 규칙은 에이전트가 무시할 수 있으므로, 훅 구현이 필요한지 명시적으로 기록합니다.

#### 실습 B: 중복 SQL 로직 통합

엔트로피 인벤토리에서 "중복된 SQL 로직" 항목이 있다면, dbt 모델로 통합합니다.

```sql
-- models/marts/fct_weekly_retention.sql
-- 역할: 주간 리텐션율 계산 (marimo 노트북에서 직접 계산하던 로직을 모델로 이동)
-- 변경 이유: 노트북과 dbt 모델에 같은 리텐션 계산 로직이 중복되어 있었음
--           → dbt 모델로 단일화하여 불일치 방지

WITH cohort_base AS (
  SELECT
    user_id,
    DATE_TRUNC(first_active_date, WEEK) AS cohort_week,
    first_active_date
  FROM {{ ref('fct_daily_active_users') }}
  WHERE first_active_date IS NOT NULL
),

user_activity AS (
  SELECT
    user_id,
    activity_date
  FROM {{ ref('fct_daily_active_users') }}
),

retention AS (
  SELECT
    cb.cohort_week,
    DATE_DIFF(ua.activity_date, cb.first_active_date, DAY) / 7 AS week_number,
    COUNT(DISTINCT ua.user_id) AS retained_users,
    COUNT(DISTINCT cb.user_id) AS cohort_size
  FROM cohort_base cb
  LEFT JOIN user_activity ua
    ON cb.user_id = ua.user_id
    AND ua.activity_date >= cb.first_active_date
  GROUP BY 1, 2
)

SELECT
  cohort_week,
  week_number,
  retained_users,
  cohort_size,
  SAFE_DIVIDE(retained_users, cohort_size) AS retention_rate
FROM retention
WHERE week_number BETWEEN 0 AND 4
```

> **핵심 원칙**: 분석 로직은 가능한 한 dbt 모델에 단일화합니다. marimo 노트북은 **시각화와 해석**에 집중하고, 데이터 변환은 dbt에 위임합니다. 이렇게 하면 로직 중복으로 인한 엔트로피를 원천 차단합니다.

#### 실습 C: 고아 파일 정리

```bash
# 정리 스프린트 — 고아 파일 탐지 및 정리
echo "=== 정리 스프린트 시작 ==="

# 1. 30일 이상 수정되지 않은 노트북 파일 목록
echo "--- 30일 이상 미수정 노트북 ---"
find notebooks/ -name "*.py" -mtime +30 -print 2>/dev/null | while read f; do
  echo "  📁 $f (마지막 수정: $(stat -f '%Sm' -t '%Y-%m-%d' "$f" 2>/dev/null || stat -c '%y' "$f" 2>/dev/null | cut -d' ' -f1))"
done

# 2. evidence/ 디렉토리에서 현재 이슈와 연결되지 않은 파일
echo "--- 연결 없는 evidence 파일 ---"
for f in evidence/*.md evidence/*.json; do
  [ -f "$f" ] || continue
  # 파일명에서 이슈 번호 추출 시도
  ISSUE_NUM=$(echo "$f" | grep -oP '\d+' | head -1)
  if [ -n "$ISSUE_NUM" ]; then
    # 이슈가 이미 닫혀 있으면 아카이브 대상
    STATE=$(gh issue view "$ISSUE_NUM" --json state -q '.state' 2>/dev/null || echo "NOT_FOUND")
    if [ "$STATE" = "CLOSED" ] || [ "$STATE" = "NOT_FOUND" ]; then
      echo "  🗑️  $f (이슈 #${ISSUE_NUM}: ${STATE})"
    fi
  fi
done

# 3. settings.json에 등록되지 않은 훅 스크립트
echo "--- 미등록 훅 스크립트 ---"
for f in .claude/hooks/*.sh; do
  [ -f "$f" ] || continue
  BASENAME=$(basename "$f")
  if ! grep -q "$BASENAME" .claude/settings.json 2>/dev/null; then
    echo "  ⚠️  $f — settings.json에 미등록"
  fi
done

echo "=== 정리 스프린트 완료 ==="
```

### 점진적 자율성 (Progressive Autonomy) 설계

에이전트의 자율성 수준은 처음부터 높게 설정하는 것이 아니라, **신뢰가 축적되면서 점진적으로 확대**합니다. 이 섹션에서는 자율성 수준을 결정하는 프레임워크와 DAU/MAU 프로젝트에 적용하는 구체적인 매트릭스를 설계합니다.

#### 자동화 안전성 판단 프레임워크

작업을 자동화(에이전트에게 위임)하기 전에, 다음 세 가지 기준으로 안전성을 평가합니다.

**"이 작업을 자동화해도 안전한가?" — 3가지 판단 기준:**

| 기준 | 질문 | 안전(자동화 적합) | 위험(사람 개입 필요) |
|------|------|-----------------|-------------------|
| **되돌림 가능성 (Reversibility)** | 결과를 실행 전 상태로 되돌릴 수 있는가? | Git 커밋 → `git revert`로 원복 가능, PR → 머지 전 취소 가능 | BigQuery 테이블 삭제 → 되돌리려면 백업 필요, Slack 메시지 → 발송 후 취소 불가 |
| **폭발 반경 (Blast Radius)** | 실패했을 때 영향 범위가 어디까지인가? | 분석 노트북 1개 오류 → 해당 이슈만 영향 | dbt 모델 변경 → 하류 모든 모델과 노트북 영향, settings.json 손상 → 모든 훅 비활성화 |
| **검증 가능성 (Verifiability)** | 결과의 정확성을 기계적으로 검증할 수 있는가? | JSON 스키마 검증 → `python3 -c "import json; json.load(open(...))"`, dbt test → 자동 통과/실패 | 분석 해석의 비즈니스 적절성 → 사람만 판단 가능, 시각화의 가독성 → 주관적 평가 |

**판단 흐름도:**

```
작업 식별
  │
  ├─ 되돌림 가능한가? ─── 아니오 ──→ 🔴 사람 승인 필수 (Level 0)
  │         │
  │        예
  │         │
  ├─ 폭발 반경이 작은가? ── 아니오 ──→ 🟡 사람 검토 후 자동 실행 (Level 1)
  │         │
  │        예
  │         │
  └─ 기계적 검증이 가능한가? ── 아니오 ──→ 🟡 자동 실행 + 사후 검토 (Level 2)
            │
           예
            │
           🟢 완전 자동 (Level 3)
```

#### 자율성 매트릭스 — DAU/MAU 프로젝트 적용

| 작업 | 되돌림 | 폭발 반경 | 검증 | 자율성 레벨 | 현재 설정 | 목표 설정 |
|------|--------|----------|------|-----------|----------|----------|
| 이슈 파싱 (stage:1) | ✅ 코멘트 삭제 가능 | 작음 (이슈 1개) | ✅ JSON 파싱 검증 | **Level 3** | 자동 | 자동 유지 |
| 문제 정의 (stage:2) | ✅ 파일 덮어쓰기 가능 | 작음 (evidence/ 1개 파일) | ⚠️ 내용 품질은 사람 판단 | **Level 2** | 자동 + 사후 검토 | 자동 유지 |
| 산출물 명세 (stage:3) | ✅ 파일 덮어쓰기 가능 | 작음 | ✅ JSON 스키마 검증 | **Level 3** | 자동 | 자동 유지 |
| 분석 스펙 (stage:4) | ✅ 파일 덮어쓰기 가능 | 중간 (dbt 쿼리 계획 영향) | ⚠️ 쿼리 적절성은 사람 판단 | **Level 2** | 자동 + 사후 검토 | 자동 유지 |
| 데이터 추출 (stage:5) | ⚠️ BigQuery 비용 발생 | 중간 (비용) | ✅ 비용 가드 훅 | **Level 1** | 비용 가드 훅으로 제한 | 자동 (비용 가드 유지) |
| 분석 수행 (stage:6) | ✅ 노트북 덮어쓰기 가능 | 작음 | ⚠️ 분석 품질은 사람 판단 | **Level 2** | 자동 + 사후 검토 | 자동 유지 |
| 리포트/PR 생성 (stage:7) | ✅ PR 닫기 가능 | 중간 (PR이 머지되면 영향 큼) | ✅ PR 리뷰 프로세스 | **Level 1** | 사람 PR 리뷰 필수 | 자동 (특정 조건 충족 시) |
| dbt 모델 변경 | ⚠️ 하류 모델 영향 | 큼 | ✅ dbt test | **Level 0** | 사람 승인 필수 | Level 1로 승격 검토 |
| settings.json 수정 | ⚠️ 모든 훅 영향 | 큼 | ⚠️ 구조 검증 가능하나 의미 검증 어려움 | **Level 0** | 사람만 수정 | 사람만 수정 유지 |
| AGENTS.md 수정 | ✅ Git revert 가능 | 큼 (에이전트 전체 행동 영향) | ❌ 의미 검증 불가 | **Level 0** | 사람만 수정 | 사람만 수정 유지 |

#### 시나리오 워크스루: PR 리뷰 자율성 점진 확대

아래는 PR 리뷰(stage:7 이후)에서 사람 개입을 점진적으로 줄이는 실제 시나리오입니다.

**1주차 — Level 0 (완전 수동 검토):**

```yaml
# .github/workflows/auto-analyze.yml (1주차)
# stage:7 완료 후 PR 생성 — 사람이 반드시 리뷰
- name: Create PR
  run: |
    gh pr create \
      --title "분석: ${{ env.ISSUE_TITLE }}" \
      --body "$PR_BODY" \
      --reviewer "data-team-lead" \       # 반드시 리뷰어 지정
      --label "auto-analyzed,needs-review"  # needs-review 라벨 추가
```

모든 PR에 `needs-review` 라벨이 붙고, 데이터 팀 리드가 반드시 리뷰합니다. 이 기간에 에이전트가 생성하는 PR의 패턴을 학습합니다.

**3주차 — Level 1 (조건부 자동 머지):**

3주 동안 10개 이상의 PR을 리뷰한 결과, DAU/MAU 단순 집계 분석은 항상 품질이 충분했다면:

```yaml
# .github/workflows/auto-analyze.yml (3주차)
# 조건부 자동 머지: 비용과 복잡도가 낮은 분석만
- name: Auto-merge decision
  run: |
    TOTAL_COST=$(python3 -c "
    import json
    log = json.load(open('evidence/query_cost_log.json'))
    print(sum(e['cost_usd'] for e in log))
    ")
    FILE_COUNT=$(git diff --name-only main...HEAD | wc -l)

    # 조건: 총 비용 $0.10 미만 AND 변경 파일 5개 이하
    if (( $(echo "$TOTAL_COST < 0.10" | bc -l) )) && [ "$FILE_COUNT" -le 5 ]; then
      echo "AUTO_MERGE=true" >> $GITHUB_ENV
      gh pr edit $PR_NUMBER --remove-label "needs-review"
      gh pr edit $PR_NUMBER --add-label "auto-approved"
    else
      echo "AUTO_MERGE=false" >> $GITHUB_ENV
      gh pr edit $PR_NUMBER --add-label "needs-review"
    fi

- name: Auto-merge if approved
  if: env.AUTO_MERGE == 'true'
  run: gh pr merge $PR_NUMBER --squash --auto
```

**6주차 — Level 2 (대부분 자동, 예외만 검토):**

```yaml
# 대부분의 분석 PR은 자동 머지, 아래 조건일 때만 사람 검토 요청:
# - 새로운 dbt 모델이 추가된 경우
# - BigQuery 비용이 $0.50 초과
# - marimo 노트북이 3개 이상 변경된 경우
- name: Escalation check
  run: |
    NEW_MODELS=$(git diff --name-only main...HEAD | grep "^models/" | grep -v "test" | wc -l)
    NOTEBOOK_CHANGES=$(git diff --name-only main...HEAD | grep "^notebooks/" | wc -l)

    if [ "$NEW_MODELS" -gt 0 ] || \
       (( $(echo "$TOTAL_COST > 0.50" | bc -l) )) || \
       [ "$NOTEBOOK_CHANGES" -gt 3 ]; then
      gh pr edit $PR_NUMBER --add-label "needs-review"
      gh pr comment $PR_NUMBER --body "⚠️ 자동 머지 조건 미충족: 사람 검토가 필요합니다.
      - 새 dbt 모델: ${NEW_MODELS}개
      - 비용: \$${TOTAL_COST}
      - 노트북 변경: ${NOTEBOOK_CHANGES}개"
    else
      gh pr merge $PR_NUMBER --squash --auto
    fi
```

> **핵심 원칙**: 자율성 확대는 항상 **데이터 기반**입니다. "에이전트를 믿으니까"가 아니라, "지난 N회의 실행에서 이 유형의 작업은 100% 정확했으므로"라는 근거가 있어야 합니다. 매트릭스의 "목표 설정"은 충분한 실행 이력이 축적된 후에만 적용합니다.

### 하니스 유지보수 루틴

엔트로피는 한 번 정리한다고 끝나지 않습니다. 정기적인 유지보수 루틴을 설정하여 엔트로피 축적을 조기에 발견하고 수정합니다.

#### 주간 유지보수 체크리스트

매주 금요일(또는 스프린트 마지막 날) 15~20분을 투자합니다.

```markdown
## 주간 하니스 유지보수 체크리스트

### 에이전트 생성 PR 패턴 점검 (5분)
- [ ] 지난 주 에이전트 생성 PR 목록 확인:
      `gh pr list --label "auto-analyzed" --state merged --json number,title,createdAt | head -20`
- [ ] PR 코멘트에서 반복적인 수정 요청 패턴이 있는지 확인
      (같은 피드백이 3회 이상 반복되면 → AGENTS.md 규칙 또는 프롬프트 수정 필요)
- [ ] 거부(reject)된 PR이 있다면 원인 분류:
      - 데이터 품질 문제 → dbt test 추가
      - 분석 방법론 문제 → 프롬프트 보강
      - 형식/스타일 문제 → AGENTS.md 규칙 추가

### 훅 실행 로그 점검 (5분)
- [ ] 비용 로그 합계 확인:
      `python3 scripts/daily_cost_report.py --date $(date -v-7d +%Y-%m-%d)`
      (주간 합계가 이전 주 대비 200% 이상 증가했다면 원인 조사)
- [ ] 비용 가드 차단 횟수 확인:
      `grep -c "쿼리 차단" logs/bq_cost.log` (0이 아니면 차단 원인 분석)
- [ ] 오류 분류 통계 확인:
      `grep -c "RETRYABLE\|ESCALATE" logs/bq_cost.log`

### 규칙 일관성 점검 (5분)
- [ ] `bash scripts/detect_agents_drift.sh` 실행 → 불일치 0건 확인
- [ ] 이번 주에 추가/수정된 dbt 모델이 있다면 sources.yml 동기화 확인
- [ ] 새로 추가된 훅 스크립트가 settings.json에 등록되어 있는지 확인
```

#### 월간 유지보수 체크리스트

매월 첫 번째 월요일에 30~45분을 투자합니다.

```markdown
## 월간 하니스 유지보수 체크리스트

### AGENTS.md 갱신 (15분)
- [ ] 지난 달 인시던트(에이전트 오류, 비용 초과, 잘못된 분석) 목록 작성
- [ ] 각 인시던트에서 도출된 새 규칙을 AGENTS.md에 추가
      예: "리텐션 분석 시 코호트 크기가 100 미만이면 통계적 유의성 경고를 포함하세요"
- [ ] 더 이상 유효하지 않은 규칙 제거 또는 "deprecated" 표시
- [ ] 규칙마다 "강제 수단" 필드 확인 — 훅이 있는지, 없다면 필요한지 판단

### 비용 추세 검토 (10분)
- [ ] 월간 BigQuery 비용 합계 계산:
      `python3 -c "
      from pathlib import Path
      import re
      total = 0
      for line in Path('logs/bq_cost.log').read_text().splitlines():
          match = re.search(r'\\\$([\d.]+)', line)
          if match: total += float(match.group(1))
      print(f'월간 총 비용: \${total:.4f}')
      "`
- [ ] 비용이 전월 대비 150% 이상 증가했다면:
      - 가장 비싼 쿼리 상위 5개 확인
      - 파티션 필터 누락 여부 검사
      - 비용 가드 임계값 조정 필요성 검토
- [ ] 비용/이슈 비율 계산 (이슈 1건당 평균 비용)

### 미사용 스킬 정리 (10분)
- [ ] `.claude/commands/` 디렉토리의 모든 커맨드 파일 목록 확인
- [ ] 지난 달 사용되지 않은 커맨드 파일 식별:
      `for cmd in .claude/commands/*.md; do
        NAME=$(basename "$cmd" .md)
        USED=$(gh issue list --state closed --search "$NAME" --json number | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        echo "$cmd: 지난 달 사용 ${USED}회"
      done`
- [ ] 사용 0회 커맨드: 삭제하거나 `_archive/` 디렉토리로 이동
- [ ] 훅 스크립트 중 settings.json에서 주석 처리(비활성화)된 것 정리
```

#### 분기 유지보수 체크리스트

분기(3개월)마다 1~2시간을 투자합니다.

```markdown
## 분기 하니스 유지보수 체크리스트

### 자동화 분류 재평가 (30분)
- [ ] 자율성 매트릭스의 모든 작업에 대해 지난 분기 실행 통계 수집:
      - 성공률, 사람 개입 횟수, 평균 비용
- [ ] Level 0/1 작업 중 Level 2/3으로 승격 가능한 항목 식별
      (조건: 지난 분기 성공률 95% 이상, 사람 개입 0회)
- [ ] Level 2/3 작업 중 강등이 필요한 항목 식별
      (조건: 오류 또는 부적절한 결과가 2회 이상 발생)
- [ ] 매트릭스 갱신 후 팀 리뷰

### 데이터 계약 갱신 (30분)
- [ ] sources.yml의 모든 소스 테이블이 아직 유효한지 확인:
      `dbt source freshness`
- [ ] 새로 추가된 BigQuery 테이블 중 sources.yml에 미등록된 것 확인
- [ ] 컬럼 스키마 변경 여부 확인:
      `bq show --schema --format=json project.dataset.table` 출력과 sources.yml 비교
- [ ] 데이터 계약(description, tests)의 정확성 검토

### 하니스 전체 건강도 점검 (30분)
- [ ] 전체 파이프라인 "스모크 테스트" 실행:
      간단한 분석 이슈 생성 → 7단계 완주 확인 → PR 품질 확인
- [ ] GitHub Actions 워크플로 실행 시간 추세 확인:
      `gh run list --workflow=auto-analyze.yml --json databaseId,conclusion,createdAt --limit 20`
- [ ] Claude Agent SDK 버전 업데이트 필요 여부 확인
- [ ] 훅 스크립트의 외부 의존성(python3, bc, jq 등) 버전 호환성 확인
```

### 2단계 자기 점검

- [ ] AGENTS.md의 규칙을 최소 2개 이상 갱신하고, 각 갱신에 날짜와 근거를 기록했다
- [ ] 중복된 SQL 로직이 있다면 dbt 모델로 통합했다 (또는 중복이 없음을 확인했다)
- [ ] 정리 스프린트 스크립트를 실행하여 고아 파일을 정리했다
- [ ] 자율성 매트릭스에서 최소 1개 작업의 레벨 변경을 제안하고 근거를 기록했다
- [ ] 주간/월간/분기 유지보수 체크리스트를 프로젝트 루트에 `MAINTENANCE.md`로 저장했다

---

## 3단계: 창작 (create)

> **이 단계의 목표**: 자신의 프로젝트에 맞는 유지보수 루틴과 자율성 매트릭스를 처음부터 설계한다.

### 창작 실습 5: 나만의 유지보수 루틴 설계

지금까지의 실습에서 사용한 체크리스트를 기반으로, 자신의 프로젝트 상황에 맞는 유지보수 루틴을 설계합니다.

**설계 가이드:**

```markdown
# [프로젝트명] 하니스 유지보수 루틴

## 프로젝트 컨텍스트
- 분석 이슈 빈도: 주 ___건
- 데이터 소스 수: ___개
- dbt 모델 수: ___개
- 에이전트 생성 PR 월간 수: ___건
- BigQuery 월간 예산: $___

## 유지보수 주기 결정
(이슈 빈도에 따라 주기 조정)
- 주 5건 이상 → 주간 체크리스트 필수 + 일간 비용 모니터링
- 주 1~4건   → 주간 체크리스트 + 월간 깊은 검토
- 월 1~4건   → 격주 체크리스트 + 분기 검토

## 주간 체크리스트 (커스텀)
- [ ] ___
- [ ] ___
- [ ] ___

## 월간 체크리스트 (커스텀)
- [ ] ___
- [ ] ___

## 분기 체크리스트 (커스텀)
- [ ] ___
- [ ] ___

## 엔트로피 알림 자동화
(선택 사항: 주간 체크리스트의 일부를 GitHub Actions cron으로 자동화)
```

### 창작 실습 6: 자율성 매트릭스 설계

DAU/MAU 프로젝트를 넘어서, **새로운 분석 시나리오**에 대한 자율성 매트릭스를 설계합니다.

**시나리오: "사용자 이탈 예측 분석" 파이프라인**

이 시나리오에서는 머신러닝 모델 학습이 포함되므로 DAU/MAU보다 복잡합니다. 각 작업에 대해 3가지 판단 기준(되돌림, 폭발 반경, 검증)을 적용하여 자율성 레벨을 결정하세요.

```markdown
# 이탈 예측 분석 — 자율성 매트릭스

| 작업 | 되돌림 | 폭발 반경 | 검증 | 자율성 레벨 | 근거 |
|------|--------|----------|------|-----------|------|
| 피처 엔지니어링 SQL 작성 | | | | | |
| ML 학습 데이터셋 생성 (BQ → CSV) | | | | | |
| 모델 학습 (scikit-learn) | | | | | |
| 예측 결과 BQ 적재 | | | | | |
| 이탈 위험 대시보드 생성 | | | | | |
| Slack 알림 (이탈 위험 사용자 목록) | | | | | |
```

> **힌트**: "예측 결과 BQ 적재"는 되돌림이 어렵고 폭발 반경이 큽니다 (다른 팀이 이 테이블을 참조할 수 있음). "Slack 알림"은 되돌림이 불가능합니다 (발송 후 취소 불가). 이 두 작업은 Level 0 또는 1이어야 합니다.

### 창작 실습 7: 엔트로피 알림 자동화

주간 체크리스트의 핵심 항목을 GitHub Actions cron 잡으로 자동화합니다. 매주 월요일 아침에 자동으로 엔트로피 신호를 탐지하고 이슈를 생성합니다.

```yaml
# .github/workflows/harness-health-check.yml
name: 하니스 건강도 점검

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 09:00 UTC (한국 시간 18:00)
  workflow_dispatch:        # 수동 실행도 가능

jobs:
  health-check:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: AGENTS.md 불일치 탐지
        id: drift
        run: |
          DRIFT_OUTPUT=$(bash scripts/detect_agents_drift.sh 2>&1)
          DRIFT_COUNT=$(echo "$DRIFT_OUTPUT" | grep -c "⚠️")
          echo "drift_count=$DRIFT_COUNT" >> $GITHUB_OUTPUT
          echo "drift_output<<EOF" >> $GITHUB_OUTPUT
          echo "$DRIFT_OUTPUT" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: 미등록 훅 탐지
        id: hooks
        run: |
          UNREGISTERED=""
          for f in .claude/hooks/*.sh; do
            [ -f "$f" ] || continue
            BASENAME=$(basename "$f")
            if ! grep -q "$BASENAME" .claude/settings.json 2>/dev/null; then
              UNREGISTERED="$UNREGISTERED\n- $f"
            fi
          done
          if [ -n "$UNREGISTERED" ]; then
            echo "unregistered=true" >> $GITHUB_OUTPUT
            echo "unregistered_list<<EOF" >> $GITHUB_OUTPUT
            echo -e "$UNREGISTERED" >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
          else
            echo "unregistered=false" >> $GITHUB_OUTPUT
          fi

      - name: 비용 추세 확인
        id: cost
        run: |
          if [ -f logs/bq_cost.log ]; then
            LAST_WEEK_COST=$(python3 -c "
          from pathlib import Path
          from datetime import datetime, timedelta
          import re
          cutoff = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
          total = 0
          for line in Path('logs/bq_cost.log').read_text().splitlines():
              if line[:10] >= cutoff:
                  match = re.search(r'\\\$([\d.]+)', line)
                  if match: total += float(match.group(1))
          print(f'{total:.4f}')
          ")
            echo "weekly_cost=$LAST_WEEK_COST" >> $GITHUB_OUTPUT
          else
            echo "weekly_cost=N/A" >> $GITHUB_OUTPUT
          fi

      - name: 건강도 이슈 생성
        if: steps.drift.outputs.drift_count != '0' || steps.hooks.outputs.unregistered == 'true'
        run: |
          gh issue create \
            --title "🔧 주간 하니스 건강도 점검 — $(date +%Y-%m-%d)" \
            --label "maintenance" \
            --body "## 하니스 건강도 자동 점검 결과

          ### AGENTS.md 불일치
          \`\`\`
          ${{ steps.drift.outputs.drift_output }}
          \`\`\`

          ### 미등록 훅 스크립트
          ${{ steps.hooks.outputs.unregistered == 'true' && steps.hooks.outputs.unregistered_list || '없음' }}

          ### 주간 BigQuery 비용
          \${{ steps.cost.outputs.weekly_cost }}

          ---
          > 이 이슈는 \`.github/workflows/harness-health-check.yml\`에 의해 자동 생성되었습니다."
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 창작 완료 검증 (통합과 개선)

```bash
# 1. 유지보수 루틴 문서 존재 확인
[ -f MAINTENANCE.md ] && echo "✅ MAINTENANCE.md 존재" || echo "❌ MAINTENANCE.md 없음"

# 2. 엔트로피 탐지 스크립트 존재 및 실행 가능 확인
[ -x scripts/detect_agents_drift.sh ] && echo "✅ detect_agents_drift.sh 실행 가능" || echo "❌ detect_agents_drift.sh 없거나 실행 불가"

# 3. AGENTS.md에 버전 또는 갱신 날짜가 포함되어 있는지
grep -q "v2\|갱신\|updated" AGENTS.md && echo "✅ AGENTS.md 갱신 이력 존재" || echo "⚠️ AGENTS.md 갱신 이력 없음"

# 4. 자율성 매트릭스 문서 존재
grep -q "자율성\|autonomy" evidence/module-4-retrospective.md 2>/dev/null && echo "✅ 자율성 매트릭스 기록됨" || echo "⚠️ 자율성 매트릭스 미기록"

# 5. 건강도 점검 워크플로 존재
[ -f .github/workflows/harness-health-check.yml ] && echo "✅ 건강도 점검 워크플로 존재" || echo "⚠️ 건강도 점검 워크플로 미작성 (선택 사항)"

# 6. 주간 체크리스트에 최소 5개 항목이 있는지
CHECKLIST_COUNT=$(grep -c "\- \[ \]" MAINTENANCE.md 2>/dev/null || echo "0")
echo "체크리스트 항목 수: ${CHECKLIST_COUNT} (최소 10개 권장)"
```

### 3단계 자기 점검

- [ ] 자신의 프로젝트에 맞는 유지보수 루틴(MAINTENANCE.md)을 작성했다
- [ ] 새로운 분석 시나리오에 대해 자율성 매트릭스를 설계하고, 각 레벨의 근거를 기록했다
- [ ] 엔트로피 알림 자동화 워크플로(선택 사항)를 작성하거나, 작성하지 않은 이유를 기록했다
- [ ] 전체 파이프라인을 재실행하여 2단계에서 수정한 내용이 올바르게 적용되었는지 확인했다

---

## 코스 완료 이후

모듈 4로 이 코스의 모든 모듈을 완료했습니다. 지금까지 구축한 것:

```
✅ AGENTS.md (v2)               — 에이전트 컨텍스트 파일 + 갱신 이력 (모듈 1, 4에서 갱신)
✅ .claude/settings.json        — 훅 + 권한 설정 (모듈 1~4에서 점진적 구축)
✅ .claude/commands/analyze.md  — 분석 스킬 (모듈 2)
✅ .claude/hooks/*.sh           — 비용 가드 + 오류 처리 훅 (모듈 4)
✅ .github/workflows/auto-analyze.yml — 7단계 자동 파이프라인 (모듈 3)
✅ .github/workflows/harness-health-check.yml — 하니스 건강도 자동 점검 (모듈 4)
✅ models/marts/*.sql           — dbt 마트 모델 (모듈 2, 4에서 확장)
✅ scripts/daily_cost_report.py — 비용 모니터링 스크립트 (모듈 4)
✅ scripts/detect_agents_drift.sh — 엔트로피 탐지 스크립트 (모듈 4)
✅ MAINTENANCE.md               — 하니스 유지보수 루틴 (모듈 4)
```

이 하니스(harness)를 기반으로 확장할 수 있는 방향:

1. **새로운 분석 유형 추가**: `.claude/commands/` 에 새 스킬 파일을 추가하고, 자율성 매트릭스에 새 작업 항목을 등록
2. **더 많은 데이터 소스**: `AGENTS.md`와 `models/staging/sources.yml`에 새 소스 추가 후 `detect_agents_drift.sh`로 동기화 확인
3. **Slack/Teams 알림**: `Stop` 훅에 알림 스텝 추가 (자율성 Level 주의 — 알림은 되돌림 불가)
4. **팀 확장**: 다른 팀원의 프로젝트에 동일한 유지보수 루틴을 적용하고, MAINTENANCE.md를 팀 표준으로 채택
5. **자율성 점진 확대**: 분기별 매트릭스 재평가를 통해 에이전트의 자율성 레벨을 데이터 기반으로 조정
4. **비용 예산 알림**: `daily_cost_report.py`를 cron으로 실행, 임계값 초과 시 이메일 발송
