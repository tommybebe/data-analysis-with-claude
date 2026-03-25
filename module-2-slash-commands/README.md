# 모듈 2: 슬래시 커맨드 작성

> `.claude/commands/`로 에이전트 작업을 명세화하는 방법을 배웁니다

**총 학습 시간**: 1.5~2시간

---

## 코스 전체 구조

이 모듈은 **하니스 엔지니어링 for 데이터 분석** 코스의 5개 모듈 중 하나입니다.

| 모듈 | 디렉터리 | 핵심 질문 |
|------|----------|-----------|
| 0 | `module-0-project-setup/` | 에이전트가 작업할 데이터 인프라를 어떻게 구축하는가? |
| 1 | `module-1-hooks/` | settings.json 훅으로 에이전트 정책을 어떻게 자동 실행하는가? |
| **2** | **`module-2-slash-commands/`** (지금 여기) | **슬래시 커맨드로 에이전트 작업을 어떻게 명세하는가?** |
| 3 | `module-3-orchestration/` | 권한과 워크플로로 에이전트 경계를 어떻게 설계하는가? |
| 4 | `module-4-error-handling/` | 하니스 전체를 통합한 종단간 분석 워크플로를 어떻게 운영하는가? |

> 각 모듈은 독립적으로 실행 가능합니다. 이전 모듈의 산출물은 **사전 구축 파일**로 이 디렉터리에 포함되어 있습니다.

---

## 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

1. `/analyze` 커맨드를 작성하여 분석 요청 파싱 → dbt 모델 탐색 → 비용 확인 → marimo 노트북 생성 → 증거 문서화의 전체 워크플로를 에이전트에게 명세할 수 있다
2. `$ARGUMENTS` 변수를 활용하여 동일한 커맨드가 다른 기간에 대해 다른 출력 파일을 생성하도록 동적 커맨드를 설계할 수 있다
3. `/check-cost`를 실행하여 BigQuery dry-run 비용 추정을 시각적 지표(✅ Safe / ⚠️ Warning / ❌ Dangerous)와 함께 출력할 수 있다
4. 커맨드를 순차적으로 체이닝(`/analyze` → `/validate-models` → `/generate-report`)하여 3개의 JSON 증거 파일을 생성할 수 있다

---

## 핵심 개념

### 슬래시 커맨드 (Slash Command) — 에이전트 작업 명세

슬래시 커맨드는 `.claude/commands/` 디렉터리에 위치한 마크다운 파일로, 에이전트가 특정 작업을 수행할 때 따라야 할 **구조화된 워크플로**를 정의합니다.

| 비교 항목 | 슬래시 커맨드 | 훅 (Hook) |
|-----------|-------------|-----------|
| 트리거 | 사용자가 `/command`로 직접 호출 | 이벤트 발생 시 자동 실행 |
| 역할 | 올바른 작업 절차를 **명세** | 잘못된 행동을 **차단/교정** |
| 파일 위치 | `.claude/commands/*.md` | `.claude/hooks/*.sh` |
| 이 모듈에서 | 학습자가 직접 작성 | 사전 구축 파일로 포함 |

> 훅은 "하지 마라" (방어), 커맨드는 "이렇게 해라" (공격)입니다. 이 디렉터리에 사전 구축된 훅(`.claude/hooks/`)과 이 모듈에서 작성할 커맨드가 함께 작동하여 에이전트의 행동 범위를 양방향으로 제어합니다.

### 커맨드 파일 구조

각 커맨드 파일은 다음 섹션을 포함해야 합니다:

```markdown
# /command-name — 한줄 목적 설명

상세 설명 문단

## Input
- `$ARGUMENTS`: 입력 형식과 예시

## Execution Steps
1. 단계 1 설명
2. 단계 2 설명
...

## Output
[기대 출력 형식]

## Constraints
- 준수할 규칙
- 금지 행동
```

### $ARGUMENTS 변수 — 동적 입력 처리

`$ARGUMENTS`는 사용자가 슬래시 커맨드 뒤에 입력한 텍스트로 동적 대체됩니다:

```bash
claude "/analyze 2026년 1월 DAU"
# → $ARGUMENTS = "2026년 1월 DAU"

claude "/check-cost SELECT count(*) FROM analytics.fct_daily_active_users"
# → $ARGUMENTS = "SELECT count(*) FROM analytics.fct_daily_active_users"
```

### 증거 파일 (Evidence) — JSON 산출물

슬래시 커맨드의 실행 결과는 텍스트 보고서 대신 **구조화된 JSON 파일**로 `evidence/` 디렉터리에 저장합니다:

| 증거 파일 | 생성 커맨드 | 필수 필드 |
|-----------|-----------|-----------|
| `evidence/dbt_test_results.json` | `/validate-models` | `total_tests`, `passed`, `failed` |
| `evidence/query_cost_log.json` | `/check-cost` | `estimated_bytes`, `within_threshold` |
| `evidence/report_manifest.json` | `/generate-report` | `outputs[].format`, `outputs[].path` |

---

## 사전 구축 파일 vs 학습자 생성 파일

### 사전 구축 파일 (이 디렉터리에 포함)

데이터 인프라와 훅 설정이 **사전 구축(frozen) 파일**로 포함되어 있습니다:

| 파일 | 설명 | 출처 |
|------|------|------|
| `dbt_project.yml` | dbt 프로젝트 설정 | 사전 구축 |
| `packages.yml` | dbt 패키지 의존성 | 사전 구축 |
| `models/staging/sources.yml` | BigQuery 소스 선언 | 사전 구축 |
| `models/staging/stg_events.sql` | 이벤트 정제 모델 | 사전 구축 |
| `models/staging/stg_users.sql` | 사용자 프로필 모델 | 사전 구축 |
| `models/marts/fct_daily_active_users.sql` | DAU 집계 | 사전 구축 |
| `models/marts/fct_monthly_active_users.sql` | MAU 집계 | 사전 구축 |
| `models/marts/fct_retention_cohort.sql` | 코호트 리텐션 | 사전 구축 |
| `models/staging/schema.yml` | 스테이징 테스트 | 사전 구축 |
| `models/marts/schema.yml` | 마트 테스트 | 사전 구축 |
| `scripts/generate_synthetic_data.py` | 합성 데이터 생성 | 사전 구축 |
| `scripts/load_to_bigquery.py` | BigQuery 로딩 | 사전 구축 |
| `AGENTS.md` | 에이전트 규칙 선언 | 사전 구축 |
| `.claude/settings.json` | 훅 + 권한 설정 | 사전 구축 |
| `.claude/hooks/bq-cost-guard.sh` | PreToolUse — BigQuery 비용 가드 | 사전 구축 |
| `.claude/hooks/dbt-auto-test.sh` | PostToolUse — dbt 컴파일 검증 | 사전 구축 |
| `.claude/hooks/stop-summary.sh` | Stop — 세션 요약 생성 | 사전 구축 |
| `pyproject.toml` | Python 의존성 | 이 모듈 제공 |
| `CLAUDE.md` | 에이전트 지시 파일 | 이 모듈 제공 |
| `.env.example` | 환경 변수 템플릿 | 이 모듈 제공 |
| `.claude/commands/validate.md` | 검증 커맨드 겸 슬래시 커맨드 설계 참고 템플릿 | 이 모듈 제공 |

### 학습자가 직접 생성하는 파일

다음 파일은 이 모듈에서 학습자가 직접 작성합니다:

| 파일 | 설명 | 분류 |
|------|------|------|
| `.claude/commands/analyze.md` | /analyze — 전체 분석 워크플로 명세 | 하니스 설정 |
| `.claude/commands/check-cost.md` | /check-cost — BigQuery 비용 추정 | 하니스 설정 |
| `.claude/commands/validate-models.md` | /validate-models — dbt 모델 검증 | 하니스 설정 |
| `.claude/commands/generate-report.md` | /generate-report — 보고서 생성 | 하니스 설정 |
| `analyses/analysis_dau_YYYYMM.py` | marimo 노트북 (/analyze로 생성) | 파이프라인 산출물 |
| `evidence/dbt_test_results.json` | dbt 테스트 결과 (/validate-models로 생성) | 파이프라인 산출물 |
| `evidence/query_cost_log.json` | 비용 추정 로그 (/check-cost로 생성) | 파이프라인 산출물 |
| `evidence/report_manifest.json` | 보고서 매니페스트 (/generate-report로 생성) | 파이프라인 산출물 |
| `evidence/module-2-retrospective.md` | 커맨드 설계 회고 | 하니스 효과 측정 |

---

## 시작하기

### 사전 준비

이 모듈을 시작하기 전에 다음이 준비되어 있어야 합니다:

- Python 3.11+, uv 패키지 매니저 설치
- Claude Code CLI 설치 및 인증 완료 (`claude whoami`)
- GCP 프로젝트 및 서비스 계정 키 파일 준비
- BigQuery에 합성 데이터 로딩 완료 (raw_events ~500k행, raw_users ~10k행)
- dbt 파이프라인 정상 동작 확인 (`uv run dbt run && uv run dbt test`)

> 이 디렉터리에는 dbt 모델, 훅 스크립트, settings.json 등 사전 구축 파일이 포함되어 있습니다. 환경 설정(uv, dbt, GCP)과 BigQuery 데이터 로딩만 완료하면 바로 시작할 수 있습니다.

### 환경 설정

```bash
# 1. 디렉터리 이동 및 Claude Code 실행
cd module-2-slash-commands
claude

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 GCP_PROJECT_ID와 GOOGLE_APPLICATION_CREDENTIALS 입력

# 3. Python 의존성 설치
uv sync

# 4. dbt 패키지 설치
uv run dbt deps

# 5. dbt 프로필 설정 (아직 없다면)
cp profiles.yml.example profiles.yml
# profiles.yml의 실제 경로와 프로젝트 ID를 수정

# 6. 파이프라인 정상 동작 확인
uv run dbt debug
uv run dbt run
uv run dbt test

# 7. 훅 동작 확인 (사전 구축 파일)
ls -la .claude/hooks/*.sh
cat .claude/settings.json | python -m json.tool
```

---

## 활동

### 활동 1: `.claude/commands/` 구조 이해 및 첫 번째 커맨드 *(15~20분)*

> **하니스 설정**: `.claude/commands/`에 작성하는 슬래시 커맨드 파일은 순수한 **하니스 설정**입니다.

먼저 `.claude/commands/` 디렉터리를 탐색합니다:

```bash
# 이미 존재하는 커맨드 확인
ls -la .claude/commands/
# validate.md가 사전 구축되어 있음

# validate.md 구조 분석 — 이 파일이 슬래시 커맨드의 실제 참고 템플릿입니다
cat .claude/commands/validate.md
```

> **📖 `/validate`를 참고 템플릿으로 활용하세요**: `validate.md`는 검증 도구이면서 동시에
> 슬래시 커맨드 구조의 **실제 예시**입니다. Input → Execution Steps → Output → Constraints의
> 4개 섹션 구조와, 조건부 분기, 외부 도구 활용, 행동 제한 등의 설계 패턴을 보여줍니다.
> 파일 끝의 "📖 이 파일을 커맨드 설계 참고 자료로 활용하기" 섹션에서 각 패턴이 정리되어 있습니다.
> 이후 활동에서 작성할 4개 커맨드도 이와 동일한 구조를 따릅니다.

간단한 `/hello` 커맨드를 만들어 커맨드 작동 원리를 이해합니다:

```markdown
# /hello — 인사와 프로젝트 상태 요약

프로젝트 현재 상태를 요약합니다.

## Input
- `$ARGUMENTS`: 없음 (무시)

## Execution Steps
1. dbt_project.yml에서 프로젝트 이름과 버전 확인
2. models/ 디렉터리의 모델 수 카운트
3. .claude/hooks/ 디렉터리의 활성 훅 수 카운트
4. 결과를 한국어로 요약 출력

## Output
프로젝트 상태 요약 (프로젝트명, 모델 수, 활성 훅 수)

## Constraints
- 데이터 쿼리 실행 금지
- 파일 수정 금지
```

Claude Code에서 `/hello`를 실행하여 커맨드 동작을 확인합니다. 확인 후 삭제해도 됩니다.

### 활동 2: `/analyze` 커맨드 — 전체 분석 워크플로 명세 *(25~30분)*

> **핵심 커맨드**: `/analyze`는 분석 요청을 받아 전체 워크플로를 실행하는 메인 커맨드입니다.

`.claude/commands/analyze.md`를 작성합니다. 다음 워크플로를 포함해야 합니다:

1. **입력 파싱**: `$ARGUMENTS`에서 분석 대상(DAU/MAU), 기간, 세그먼트를 추출
2. **비용 사전 확인**: 실행할 쿼리의 예상 비용을 dry-run으로 확인
3. **dbt 모델 탐색**: `models/marts/` 레이어에서 관련 모델 식별
4. **marimo 노트북 생성**: `analyses/` 디렉터리에 `analysis_[metric]_[YYYYMM].py` 형식으로 생성
5. **증거 문서화**: 분석 과정의 주요 메트릭을 JSON으로 기록

**Claude Code 프롬프트 예시**:

```bash
claude "CLAUDE.md의 슬래시 커맨드 컨셉과 marimo 컨벤션을 읽고
.claude/commands/analyze.md를 작성해줘.
$ARGUMENTS로 분석 대상과 기간을 받고,
비용 사전 확인 → dbt 모델 탐색 → marimo 노트북 생성 → 증거 기록의
전체 워크플로를 명세해줘.
Input, Execution Steps, Output, Constraints 섹션을 포함해야 해."
```

### 활동 3: `/check-cost` 커맨드 — BigQuery dry-run 비용 조회 *(15~20분)*

> **비용 의식**: BigQuery on-demand 가격은 $5/TB입니다. `/check-cost`로 쿼리 전 비용을 추정합니다.

`.claude/commands/check-cost.md`를 작성합니다:

- `$ARGUMENTS`로 SQL 쿼리 또는 자연어 쿼리 설명을 받음
- `bq query --dry_run`으로 예상 스캔 바이트 확인
- 결과를 MB/GB 단위와 USD 비용으로 변환
- 안전 판단 기준:
  - ✅ Safe: < 100MB
  - ⚠️ Warning: 100MB ~ 1GB
  - ❌ Dangerous: > 1GB (BQ_COST_LIMIT_BYTES 초과)
- `evidence/query_cost_log.json`에 결과 기록

### 활동 4: `/validate-models`와 `/generate-report` 커맨드 *(20~25분)*

**`/validate-models`** — dbt 모델 검증:
- `dbt test` 실행 후 결과를 `evidence/dbt_test_results.json`에 저장
- JSON 필수 필드: `total_tests`, `passed`, `failed`, `timestamp`

**`/generate-report`** — 보고서 생성:
- `analyses/` 디렉터리의 marimo 노트북을 HTML로 내보내기
- `marimo export html` 명령 사용
- `evidence/report_manifest.json`에 생성된 파일 목록 기록
- JSON 필수 필드: `outputs[].format`, `outputs[].path`, `timestamp`

**Claude Code 프롬프트 예시**:

```bash
claude "CLAUDE.md와 AGENTS.md를 읽고
.claude/commands/validate-models.md와
.claude/commands/generate-report.md를 작성해줘.
validate-models는 dbt test 후 evidence/dbt_test_results.json 생성,
generate-report는 marimo export html 후 evidence/report_manifest.json 생성.
두 커맨드 모두 Input, Execution Steps, Output, Constraints 섹션 포함."
```

### 활동 5: `$ARGUMENTS` 변수 활용 — 동적 커맨드 설계 *(10~15분)*

동일한 `/analyze` 커맨드를 다른 인자로 실행하여 `$ARGUMENTS`의 동적 대체를 확인합니다:

```bash
# 1월 DAU 분석
claude "/analyze 2026년 1월 DAU"
# → analyses/analysis_dau_202601.py 생성 예상

# 2월 MAU 분석
claude "/analyze 2026년 2월 MAU"
# → analyses/analysis_mau_202602.py 생성 예상

# 동일 커맨드, 다른 인자 → 다른 출력 파일
ls analyses/
```

`$ARGUMENTS` 처리의 핵심 패턴:
- 기간 추출: "2026년 1월" → `202601`
- 메트릭 식별: "DAU" → `fct_daily_active_users`, "MAU" → `fct_monthly_active_users`
- 파일명 생성: `analysis_[metric]_[YYYYMM].py`

### 활동 6: 커맨드 체이닝 연습 및 회고 *(15~20분)*

커맨드를 순차적으로 체이닝하여 완전한 분석 사이클을 실행합니다:

```bash
# 1. 분석 실행
claude "/analyze 2026년 1월 DAU"

# 2. 모델 검증
claude "/validate-models"

# 3. 보고서 생성
claude "/generate-report"

# 4. 증거 파일 확인
ls -la evidence/
# dbt_test_results.json, query_cost_log.json, report_manifest.json 확인
```

체이닝 후 증거 파일 3개가 모두 생성되었는지 확인합니다.

---

## Claude Code 프롬프트 예제

**4개 커맨드 일괄 생성**:

```bash
claude "CLAUDE.md의 슬래시 커맨드 컨셉과 커맨드 파일 구조를 읽고
다음 4개 커맨드 파일을 .claude/commands/에 생성해줘:
1. analyze.md — $ARGUMENTS로 분석 대상·기간을 받아 비용 확인 → dbt 모델 탐색 → marimo 노트북 생성
2. check-cost.md — $ARGUMENTS로 SQL을 받아 bq dry-run → MB/GB·USD 비용 출력 → 안전 판단
3. validate-models.md — dbt test 실행 → evidence/dbt_test_results.json 생성
4. generate-report.md — marimo export html → evidence/report_manifest.json 생성
각 파일에 Input, Execution Steps, Output, Constraints 섹션 포함."
```

**커맨드 구조 검증**:

```bash
claude "내가 작성한 4개 슬래시 커맨드(.claude/commands/ 안의 analyze, check-cost,
validate-models, generate-report)를 검토해줘.
각 커맨드에 Input/Execution Steps/Output/Constraints 4개 섹션이 모두 있는지,
$ARGUMENTS 변수를 적절히 활용하는지,
evidence/ 디렉터리에 JSON 증거 파일을 생성하는지 확인해줘."
```

---

## 관찰-수정-창작 사이클

### 관찰 (observe)

커맨드 없이 에이전트에게 분석을 요청했을 때와 `/analyze`를 사용했을 때의 차이를 관찰합니다:

- 커맨드 없음: 에이전트가 자체 판단으로 절차를 결정 (추론/speculation 발생)
- `/analyze` 사용: 명세된 절차를 순서대로 수행 (일관된 출력)

### 회고 질문

아래 질문에 대한 답변을 `evidence/module-2-retrospective.md`에 기록하세요.

**영역 A: 에이전트 추론(speculation) 분석**

1. **커맨드 없는 요청 vs 커맨드 사용**: "1월 DAU를 분석해줘"라고만 요청했을 때 에이전트가 어떤 절차를 자체 결정했는가? `/analyze`를 사용했을 때와 어떤 차이가 있었는가?
2. **추론의 위험성**: 에이전트가 자체 판단한 절차 중 비용이나 보안 관점에서 위험한 것이 있었는가?

**영역 B: 커맨드-훅 역할 분담**

3. **명세 vs 방어**: `/analyze` 커맨드가 "이렇게 해라"를 명세하고, `bq-cost-guard.sh` 훅이 "한도 초과 시 차단"을 실행합니다. 이 두 계층이 겹치는 부분과 보완하는 부분은?
4. **단독 사용 한계**: 커맨드만 있고 훅이 없다면, 또는 훅만 있고 커맨드가 없다면 어떤 문제가 발생하는가?

**영역 C: 동적 커맨드 설계**

5. **$ARGUMENTS 설계**: `$ARGUMENTS`를 통해 받는 입력의 형식을 어떻게 정의했는가? 잘못된 형식의 입력이 들어왔을 때 커맨드가 어떻게 대응하는가?

### 창작 (create)

회고 결과를 바탕으로:
1. `/analyze` 커맨드에 입력 검증 단계를 추가 — 잘못된 `$ARGUMENTS`에 대한 에러 메시지
2. `/check-cost`의 안전 판단 기준을 환경변수(`BQ_COST_LIMIT_BYTES`)와 연동
3. 커맨드 체이닝을 자동화하는 `/full-analysis` 메타 커맨드 설계 (선택)

---

## 완료 체크리스트

> 6개 항목 **모두 합격**이어야 이 모듈을 완료한 것입니다.

### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | 4개 커맨드 파일 | `.claude/commands/{analyze,check-cost,validate-models,generate-report}.md` | 하니스 설정 |
| 2 | marimo 노트북 | `analyses/analysis_dau_YYYYMM.py` | 파이프라인 산출물 |
| 3 | dbt 테스트 증거 | `evidence/dbt_test_results.json` (`total_tests`, `passed`, `failed`) | 파이프라인 산출물 |
| 4 | 비용 로그 증거 | `evidence/query_cost_log.json` (`estimated_bytes`, `within_threshold`) | 파이프라인 산출물 |
| 5 | 보고서 매니페스트 | `evidence/report_manifest.json` (`outputs[].format`, `outputs[].path`) | 파이프라인 산출물 |
| 6 | 회고 기록 | `evidence/module-2-retrospective.md` — 추론 분석 + 커맨드-훅 연계 | 하니스 효과 측정 |

### 자가 점검

**[점검 1/6]** 슬래시 커맨드 파일 4개 존재 및 구조 검증
```bash
for cmd in analyze check-cost validate-models generate-report; do
  echo "=== $cmd ===" && head -5 .claude/commands/$cmd.md
done
# ✅ 합격: 4개 파일 모두 존재하고 제목 행 출력됨
```

**[점검 2/6]** /analyze 커맨드 구조 확인
```bash
grep -c -E '(\$ARGUMENTS|analyses/|fct_daily_active_users|fct_monthly_active_users|비용|cost)' .claude/commands/analyze.md
# ✅ 합격: 3개 이상 매칭 (입력 변수, 출력 경로, 모델 참조)
```

**[점검 3/6]** /check-cost 비용 추정 구조 확인
```bash
grep -c -E '(dry_run|dry-run|MB|GB|Safe|Warning|Dangerous|query_cost_log)' .claude/commands/check-cost.md
# ✅ 합격: 3개 이상 매칭
```

**[점검 4/6]** /validate-models 테스트 결과 JSON 구조 확인
```bash
grep -c -E '(dbt test|dbt_test_results|total_tests|passed|failed)' .claude/commands/validate-models.md
# ✅ 합격: 3개 이상 매칭
```

**[점검 5/6]** /generate-report 보고서 매니페스트 구조 확인
```bash
grep -c -E '(marimo export|report_manifest|outputs|format|path)' .claude/commands/generate-report.md
# ✅ 합격: 3개 이상 매칭
```

**[점검 6/6]** 회고 기록 존재 및 내용 확인
```bash
cat evidence/module-2-retrospective.md | head -20
# ✅ 합격: 추론(speculation) 분석과 커맨드-훅 역할 분담 내용 포함
```

---

## 완료 확인

> `/validate` 명령으로 모듈 완료 상태를 확인할 수 있습니다.
