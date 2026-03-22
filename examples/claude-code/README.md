# Claude Code 하니스 예시

> 데이터 분석 워크플로에서 Claude Code를 에이전트로 활용하기 위한 설정 파일 모음

이 디렉토리는 모듈 2(스킬과 훅)에서 학습하는 Claude Code 하니스 설정의 **완성된 예시**입니다.
실제 프로젝트에서는 이 파일들을 `.claude/` 디렉토리에 배치합니다.

---

## 디렉토리 구조

```
.claude/
├── settings.json              # 권한 정책 + 훅 등록
├── commands/                  # 슬래시 커맨드 (스킬) 정의
│   ├── analyze.md             # /analyze — 분석 실행 (end-to-end)
│   ├── validate-models.md     # /validate-models — dbt 검증
│   ├── generate-report.md     # /generate-report — 리포트 생성
│   ├── check-cost.md          # /check-cost — 비용 확인
│   ├── explore-data.md        # /explore-data — 데이터 탐색
│   ├── create-model.md        # /create-model — dbt 모델 생성
│   ├── create-notebook.md     # /create-notebook — marimo 노트북 생성
│   └── setup-harness.md       # /setup-harness — 하니스 환경 초기화
└── hooks/                     # 자동 실행 스크립트
    ├── bq-cost-guard.sh        # PreToolUse: BigQuery 비용 가드
    ├── dbt-auto-test.sh        # PostToolUse: dbt 자동 테스트
    ├── marimo-check.sh         # PostToolUse: marimo 노트북 유효성 검사
    ├── query-logger.sh         # PostToolUse: 쿼리 비용 로그 기록
    ├── pre-commit-dbt-check.sh # git pre-commit: 커밋 전 검증
    └── stop-summary.sh         # Stop: 작업 완료 요약
```

---

## settings.json — 핵심 설정 파일

`.claude/settings.json`은 Claude Code의 **세 가지 핵심 정책**을 정의합니다.

### 1. 권한 (permissions)

```json
{
  "permissions": {
    "allow": ["Bash(dbt run:*)", "Bash(bq query --dry_run:*)", "Read", "Write", "Edit"],
    "deny": ["Bash(dbt run --full-refresh:*)", "Bash(rm -rf:*)", "Bash(bq rm:*)"]
  }
}
```

**allow**: 에이전트가 승인 없이 실행할 수 있는 명령어
**deny**: 명시적으로 차단하는 명령어 (사용자 확인도 불가)

> **설계 원칙**: deny 목록은 "실수로 실행하면 복구 불가능한" 명령어만 포함합니다.
> `dbt run --full-refresh`는 전체 테이블 재빌드로 큰 비용을 유발할 수 있어 차단합니다.

### 2. 훅 (hooks)

훅은 특정 이벤트에 **자동으로 실행되는 검증 스크립트**입니다.

| 이벤트 | 타이밍 | 예시 사용처 |
|--------|--------|------------|
| `PreToolUse` | 도구 실행 **직전** | BigQuery 비용 검사 |
| `PostToolUse` | 도구 실행 **직후** | dbt 자동 테스트, marimo 유효성 검사, 쿼리 비용 로깅 |
| `Stop` | Claude 응답 **완료 후** | 작업 산출물 요약 |

> **중요**: 훅 스크립트는 STDIN으로 JSON 입력을 받습니다.
> `settings.json`의 hook `command`에 인자를 추가하지 마세요.
> 올바른 설정: `"command": "bash .claude/hooks/bq-cost-guard.sh"`
> 잘못된 설정: `"command": "bash .claude/hooks/bq-cost-guard.sh \"$CLAUDE_TOOL_INPUT\""`

### 3. 스킬 (commands/)

`.claude/commands/` 디렉토리의 마크다운 파일이 슬래시 커맨드로 등록됩니다.

```
Claude Code 터미널에서:
> /analyze DAU가 지난 주 20% 감소했습니다. 원인을 분석해 주세요.
> /validate-models fct_daily_active_users
> /check-cost models/marts/fct_retention_cohort.sql
> /generate-report notebooks/analysis_dau_mau.py
> /explore-data fittrack_raw.events
> /create-model mart 일별 수익 집계 fct_daily_revenue
> /create-notebook DAU/MAU 트렌드 분석 지난 30일
> /setup-harness
```

---

## 스킬 상세 설명

### `/analyze` — 분석 실행

분석 요청(텍스트 또는 GitHub Issue 번호)을 받아 end-to-end 분석을 수행합니다.

**입력**: 분석 요청 설명 또는 `#이슈번호`
**출력**: dbt 모델(필요 시) + marimo 노트북 + 완료 증거 JSON

```
# 사용 예시
/analyze Issue #42의 요청대로 3월 리텐션 코호트를 분석해 주세요.
/analyze 지난 분기 신규 가입자의 첫 30일 활성도를 분석해 주세요.
```

### `/validate-models` — dbt 검증

dbt 모델을 빌드하고 모든 데이터 테스트를 실행합니다.

**입력**: 모델명 (선택, 미입력 시 전체)
**출력**: 빌드/테스트 결과 요약

```
# 사용 예시
/validate-models fct_daily_active_users
/validate-models +fct_retention_cohort  # 업스트림 포함
/validate-models                        # 전체 모델
```

### `/generate-report` — 리포트 생성

marimo 노트북을 HTML으로 내보냅니다.

**입력**: 노트북 파일 경로
**출력**: `reports/` 디렉토리에 HTML 파일

```
# 사용 예시
/generate-report notebooks/analysis_dau_mau.py
```

### `/check-cost` — 비용 확인

SQL 쿼리를 dry-run으로 실행하여 예상 스캔량과 비용을 계산합니다.

**입력**: SQL 문자열 또는 `.sql` 파일 경로
**출력**: 예상 스캔 바이트, 예상 비용(USD), 위험도 분류

```
# 사용 예시
/check-cost SELECT * FROM `project.dataset.events` WHERE DATE(ts) = '2024-01-01'
/check-cost models/marts/fct_retention_cohort.sql
```

### `/explore-data` — 데이터 탐색

BigQuery 테이블 또는 dbt 모델의 스키마와 기초 통계를 빠르게 파악합니다.

**입력**: 테이블 참조 또는 dbt 모델명
**출력**: 스키마, 행 수, 기간, 데이터 품질 체크 결과

```
# 사용 예시
/explore-data fittrack_raw.events
/explore-data fct_daily_active_users
/explore-data project.dataset.table_name
```

### `/create-model` — dbt 모델 생성

프로젝트 규약에 맞는 dbt 모델 파일을 스캐폴딩합니다.

**입력**: 모델 생성 요청 설명 (계층 + 목적)
**출력**: SQL 파일 + schema.yml 업데이트 + 빌드/테스트 결과

```
# 사용 예시
/create-model staging events 테이블에서 purchase 이벤트만 필터링
/create-model mart 일별 수익 집계 fct_daily_revenue
/create-model intermediate 사용자별 주간 활동 집계
```

### `/create-notebook` — marimo 노트북 생성 (신규)

분석 주제에 맞는 marimo 노트북 파일을 자동 스캐폴딩합니다.
BigQuery 연결, 데이터 로드, 시각화, 결론 셀까지 기본 구조를 생성합니다.

**입력**: 노트북 생성 요청 설명 또는 `#이슈번호`
**출력**: `notebooks/analysis_<이름>.py` 파일

```
# 사용 예시
/create-notebook DAU/MAU 트렌드 분석 지난 30일
/create-notebook #42 3월 코호트 리텐션 분석
/create-notebook 신규 사용자 온보딩 퍼널 분석
```

### `/setup-harness` — 하니스 환경 초기화 (신규)

새 프로젝트에서 하니스 환경을 처음 설정합니다.
필수 디렉토리, 권한, git 훅을 자동으로 구성합니다.

**입력**: (선택) `--skip-git-hooks`, `--bq-limit-gb=N`
**출력**: 디렉토리 생성, 훅 권한 설정, 환경 변수 확인

```
# 사용 예시
/setup-harness
/setup-harness --bq-limit-gb=5
/setup-harness --skip-git-hooks
```

---

## 훅 상세 설명

### `bq-cost-guard.sh` — BigQuery 비용 가드 (PreToolUse)

**이벤트**: `PreToolUse` (Bash 도구 실행 전)
**역할**: `bq query` 명령 감지 → dry-run 실행 → 1GB 초과 시 차단

```
동작 흐름:
bq query 명령 감지 (--dry_run 명령은 통과)
    → dry-run 실행
    → 스캔 바이트 추출 및 비용 계산
    → 1GB 초과? → exit 1 (실행 차단)
    → 1GB 이내? → exit 0 (실행 허용)
```

환경 변수로 한도를 조정할 수 있습니다:
```bash
# 10GB로 한도 변경
export BQ_COST_LIMIT_BYTES=10737418240
```

### `dbt-auto-test.sh` — dbt 자동 테스트 (PostToolUse)

**이벤트**: `PostToolUse` (Write/Edit 도구 실행 후)
**역할**: `.sql` 파일 수정 감지 → 해당 모델 + 다운스트림 자동 테스트

> ⚠️ 이 훅은 경고만 표시하고 작업을 차단하지 않습니다 (`exit 0`).
> 실패 메시지를 보면 Claude Code가 자동으로 수정을 시도합니다.

### `marimo-check.sh` — marimo 유효성 검사 (PostToolUse) 신규

**이벤트**: `PostToolUse` (Write/Edit 도구 실행 후)
**역할**: `notebooks/` 디렉토리의 `.py` 파일 수정 감지 → marimo 형식 검증

검증 항목:
1. Python 문법 검사 (`py_compile`)
2. `import marimo` 선언 존재 여부
3. `app = marimo.App()` 패턴 존재 여부
4. `@app.cell` 데코레이터 최소 1개 이상

### `query-logger.sh` — 쿼리 비용 로거 (PostToolUse) 신규

**이벤트**: `PostToolUse` (Bash 도구 실행 후)
**역할**: bq query 실행 후 스캔 바이트와 비용을 `.claude/logs/query-log.jsonl`에 기록

```json
{"timestamp": "2024-01-01T10:00:00Z", "command": "bq_query", "bytes_processed": 536870912, "cost_usd": 0.002441, "query_snippet": "SELECT ..."}
```

`stop-summary.sh`가 오늘의 누계 비용을 자동으로 보고합니다.

### `pre-commit-dbt-check.sh` — 커밋 전 검증 (git pre-commit)

**이벤트**: git commit 직전 (git pre-commit 훅)
**역할**: dbt 모델 변경이 포함된 커밋에서 run + test + freshness 검증

> 이 스크립트는 Claude Code 훅이 아닌 **git pre-commit 훅**입니다.
> `.git/hooks/pre-commit`에 복사하거나 `pre-commit` 패키지로 등록합니다.

```bash
# git pre-commit 훅으로 설치
cp .claude/hooks/pre-commit-dbt-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### `stop-summary.sh` — 작업 완료 요약 (Stop)

**이벤트**: `Stop` (Claude 응답 완료 후)
**역할**: 변경된 파일, dbt 테스트 결과, 생성된 노트북/리포트, **오늘의 BigQuery 비용 누계**를 자동 요약

---

## 하니스 계층 구조

```
┌─────────────────────────────────────────────────┐
│                  스캐폴딩 계층                    │
│  AGENTS.md — 규칙 선언 (what to know)            │
├─────────────────────────────────────────────────┤
│                  스킬/훅 계층                    │
│  commands/ — 재사용 가능한 작업 단위 (what to do) │
│  hooks/ — 자동 검증 및 정책 적용 (how to enforce) │
├─────────────────────────────────────────────────┤
│                 오케스트레이션 계층               │
│  GitHub Actions — 이슈 기반 자동 파이프라인       │
└─────────────────────────────────────────────────┘
```

**스캐폴딩**은 에이전트가 "알아야 할 것"을 선언하고,
**스킬/훅**은 에이전트가 "할 수 있는 것"과 "반드시 지켜야 할 것"을 코드로 보장하며,
**오케스트레이션**은 이 모든 것을 자동화합니다.

---

## 실제 프로젝트에 적용하는 방법

```bash
# 1. .claude/ 디렉토리 생성
mkdir -p .claude/commands .claude/hooks .claude/logs

# 2. 설정 파일 복사
cp examples/claude-code/settings.json .claude/settings.json
cp examples/claude-code/commands/*.md .claude/commands/
cp examples/claude-code/hooks/*.sh .claude/hooks/

# 3. 훅 스크립트 실행 권한 부여
chmod +x .claude/hooks/*.sh

# 4. git pre-commit 훅 설치 (선택)
cp .claude/hooks/pre-commit-dbt-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 5. 필수 디렉토리 생성
mkdir -p notebooks reports evidence .claude/logs

# 또는 슬래시 커맨드로 자동 초기화:
# /setup-harness
```

> **주의**: `settings.json`의 BQ 프로젝트 ID와 비용 한도를 프로젝트에 맞게 조정하세요.
> `BQ_COST_LIMIT_BYTES` 환경 변수로 기본 1GB 한도를 변경할 수 있습니다.

---

## 훅 개발 시 주의사항

### STDIN 입력 형식

모든 Claude Code 훅은 STDIN으로 JSON을 받습니다. `settings.json`의 hook command에 인자를 추가하지 마세요.

```bash
# 훅 스크립트에서 입력 읽기 (올바른 방법)
HOOK_INPUT=$(cat)

# PreToolUse 형식
# {"tool_name": "Bash", "tool_input": {"command": "..."}}

# PostToolUse 형식
# {"tool_name": "Write", "tool_input": {"file_path": "..."}, "tool_response": {...}}
```

### 훅 종료 코드

| 종료 코드 | 의미 | 사용 예시 |
|-----------|------|----------|
| `exit 0` | 성공/허용 | 경고만 표시 |
| `exit 1` | 실패/차단 | PreToolUse에서 비용 초과 차단 |
| `exit 2` | Claude에 추가 처리 요청 | (특수 상황) |

