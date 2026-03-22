# 모듈 2: 슬래시 커맨드와 AGENTS.md 작성 — 에이전트 작업 명세화

> **학습 시간**: 2~3시간
> **난이도**: 중급 (데이터 분석 실무 경험자 대상)
> **핵심 질문**: "에이전트가 매번 올바른 방식으로 분석 작업을 수행하게 하려면, 어떻게 작업을 '명세'해야 하는가?"
> **학습 구조**: 관찰(觀察) → 수정(修正) → 창작(創作) 3단계 학습 사이클

---

## 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [핵심 개념: 계층 3 서술적 정책](#2-핵심-개념-계층-3-서술적-정책)
3. [1단계: 관찰 — AGENTS.md와 슬래시 커맨드 구조 이해](#1단계-관찰--agentsmd와-슬래시-커맨드-구조-이해)
4. [2단계: 수정 — 기존 커맨드와 AGENTS.md 조정하기](#2단계-수정--기존-커맨드와-agentsmd-조정하기)
5. [3단계: 창작 — 나만의 커맨드와 AGENTS.md 작성](#3단계-창작--나만의-커맨드와-agentsmd-작성)
6. [프롬프트 엔지니어링 패턴](#6-프롬프트-엔지니어링-패턴)
7. [모듈 자기 점검 체크리스트](#7-모듈-자기-점검-체크리스트)

---

## 1. 사전 요구사항

### 1.1 환경 준비 상태 확인

이 모듈을 시작하기 전에 다음이 완료된 상태여야 합니다.

```
✅ 모듈 0 완료            — Claude Code, uv, dbt, marimo 설치 및 버전 확인
✅ 모듈 1 완료            — settings.json, PreToolUse/PostToolUse 훅 구현 완료
✅ BigQuery 데이터 적재    — raw_events, raw_users, raw_sessions 테이블 존재
✅ dbt 모델 빌드 성공     — staging 3개 + mart 3개, dbt test 0 Fail
✅ .claude/ 디렉토리 구조 — settings.json, hooks/ 폴더 생성 완료
```

`.claude/commands/` 폴더는 **아직 없는 상태**입니다. 이것이 모듈 2의 핵심 산출물 중 하나입니다.

**체크 방법**:

```bash
# .claude 구조 확인
ls -la .claude/
# 예상 출력:
# drwxr-xr-x  hooks/
# -rw-r--r--  settings.json

# AGENTS.md 존재 여부 확인
test -f AGENTS.md && echo "AGENTS.md 존재" || echo "AGENTS.md 없음 — 이 모듈에서 작성"
```

### 1.2 사전 지식 요구사항

| 영역 | 이 모듈에서 필요한 수준 | 부족하다면 |
|------|----------------------|------------|
| Markdown | 헤더, 코드 블록, 테이블 작성 가능 | GitHub Markdown 가이드 참조 |
| Claude Code 기본 사용 | `/` 명령어 입력, 파일 편집 기본 대화 경험 | 모듈 0 활동 7 재실행 |
| 프롬프트 작성 경험 | LLM에게 구조화된 요청을 해본 경험 | 필수는 아님, 이 모듈에서 학습 |
| 데이터 분석 도메인 지식 | DAU/MAU 개념 이해, BigQuery SQL 작성 경험 | 코스 사전 요구사항 참조 |
| settings.json 구조 | 훅 이벤트 유형, JSON 스키마 이해 | 모듈 1 복습 |

### 1.3 이 모듈에서 다루지 않는 것

- 훅(hook) 스크립트 작성 → 모듈 1에서 다뤘습니다
- 권한(permissions) 상세 설계 → 모듈 3에서 다룹니다
- GitHub Actions 워크플로 연결 → 모듈 4에서 다룹니다

**하니스 vs. 파이프라인 산출물 구분**: 이 모듈에서 여러분이 작성하는 `AGENTS.md`와 슬래시 커맨드 파일들은 **하니스 설정(harness configuration)** 입니다 — 에이전트에게 "어떻게 일하라"는 지침을 제공하는 것이지, 분석 결과 자체가 아닙니다. 에이전트가 이 지침을 읽고 실행하여 만들어 내는 DAU/MAU 차트, dbt 결과물, marimo 리포트가 **파이프라인 산출물**입니다.

### 1.4 3단계 학습 사이클 안내

이 모듈은 **관찰(관찰) → 수정(수정) → 창작(창작)** 3단계로 구성됩니다.

```
1단계: 관찰 — 스타터 레포의 AGENTS.md와 슬래시 커맨드를 읽고 분석합니다
              "이것은 어떻게 구성되어 있는가?"
              (예상 소요: 45~55분)

2단계: 수정 — 기존 AGENTS.md와 DAU 커맨드를 프로젝트 요구에 맞게 조정합니다
              "이것을 우리 프로젝트에 맞게 바꾸면?"
              (예상 소요: 40~50분)

3단계: 창작 — MAU 커맨드와 완성된 AGENTS.md를 처음부터 작성합니다
              "이것을 없는 상태에서 만들려면?"
              (예상 소요: 50~60분)
```

---

## 2. 핵심 개념: 계층 3 서술적 정책

### 2.1 세 정책 계층 복습

모듈 1에서 소개한 하니스의 세 정책 계층을 다시 살펴봅니다.

```
계층 1: 선언적 정책 (settings.json > permissions)
  → "에이전트는 DROP TABLE을 절대 실행할 수 없다"
  → 허용/거부 패턴 목록으로 정의 [모듈 1 완료]

계층 2: 절차적 정책 (settings.json > hooks)
  → "BigQuery 쿼리 실행 전 반드시 비용 확인"
  → 훅 스크립트로 런타임에 검사 [모듈 1 완료]

계층 3: 서술적 정책 (AGENTS.md, 슬래시 커맨드)        ← 이 모듈
  → "분석 요청은 항상 날짜 범위를 명시하라"
  → 에이전트가 읽는 텍스트 지침
```

계층 3은 계층 1·2와 달리 **기계적 강제력이 없습니다**. 에이전트가 프롬프트를 읽고 따르길 "기대"하는 것입니다.

### 2.2 서술적 정책이 필요한 이유

계층 1과 2는 **"하면 안 되는 것"을 막는** 데 효과적입니다. 그러나 **"어떻게 잘 해야 하는가"를 안내**하는 데는 텍스트 지침이 더 적합합니다.

예를 들어:
- "BigQuery 쿼리에서 파티션 필터는 항상 `event_date` 컬럼 기준으로 사용하라" — 훅으로 강제하기 어렵습니다.
- "dbt 테스트가 실패하면 수정하지 말고 사람에게 보고하라" — 허용/거부 패턴으로 표현할 수 없습니다.
- "MAU 계산에서 활성 사용자의 정의는 해당 월에 최소 1개 이상의 유효 이벤트를 발생시킨 사용자이다" — 도메인 지식으로, 코드로 강제하는 것보다 명시적으로 문서화하는 것이 적합합니다.

> **핵심 통찰**: 계층 1·2는 **가드레일(guardrail)** 이고, 계층 3은 **내비게이션(navigation)** 입니다. 가드레일이 충돌을 막는다면, 내비게이션은 올바른 방향으로 안내합니다.

### 2.3 서술적 정책의 두 형태

| 형태 | 파일 위치 | 적용 범위 | 역할 |
|------|-----------|-----------|------|
| **에이전트 컨텍스트 파일 (AGENTS.md)** | 레포 루트 `/AGENTS.md` | 모든 에이전트 세션 | 레포 전역 규칙, 도메인 정의, 아키텍처 설명 |
| **슬래시 커맨드 (slash command)** | `.claude/commands/*.md` | 특정 작업 실행 시 | 단일 작업의 입력·절차·출력 명세 |

---

## 1단계: 관찰 — AGENTS.md와 슬래시 커맨드 구조 이해

> **목표**: 스타터 레포의 AGENTS.md와 슬래시 커맨드 파일을 읽고 분석하여, 서술적 정책이 어떻게 구성되는지 이해합니다. 이 단계에서는 코드를 **작성하지 않습니다** — 읽고 질문하고 이해합니다.

### 관찰 1-A: AGENTS.md란 무엇이고 어떻게 동작하는가

```bash
# 스타터 레포 AGENTS.md 읽기
cat AGENTS.md
```

`AGENTS.md`는 **에이전트가 이 레포지토리에서 작업할 때 항상 참조하는 맥락 문서**입니다. 사람이 읽는 `README.md`가 아니라, 에이전트가 읽는 "이 레포에서 올바르게 일하는 방법"입니다.

Claude Code는 프로젝트 디렉토리에서 세션을 시작할 때 `AGENTS.md`를 자동으로 로드합니다. 따라서 수강생이 매번 "우리 프로젝트에서는..." 같은 설명을 반복할 필요가 없습니다.

**비유**: AGENTS.md는 신입 팀원이 입사 첫날 받는 "팀 온보딩 문서"와 같습니다. 그러나 그 팀원이 AI 에이전트이므로, 문서는 다음을 명확히 해야 합니다:
- 이 레포에서 에이전트가 **해도 되는 것**과 **하면 안 되는 것**
- 에이전트가 모르면 안 되는 **도메인 정의**
- 에이전트가 따라야 할 **절차적 규약**

**관찰 질문 1**: 스타터 레포의 AGENTS.md에는 몇 개의 주요 섹션이 있는가? 각 섹션이 다루는 내용은?

**관찰 질문 2**: "활성 사용자(Active User)"의 정의가 얼마나 구체적으로 작성되어 있는가? `event_type` 기준이 명시되어 있는가?

### 관찰 1-B: 효과적인 AGENTS.md의 5개 섹션 구조

효과적인 `AGENTS.md`는 다음 5개 섹션으로 구성됩니다. 스타터 레포의 파일과 비교하며 각 섹션의 역할을 이해합니다.

**섹션 1: 프로젝트 개요 (Project Overview)**

에이전트가 이 레포의 목적과 전체 데이터 흐름을 이해하도록 돕습니다.

```markdown
## 프로젝트 개요

이 레포는 B2C 모바일 앱의 DAU/MAU 분석 파이프라인을 관리합니다.

**데이터 흐름**:
raw_events (BigQuery) → stg_events (dbt staging) → fct_daily_active_users (dbt mart) → marimo 리포트

**에이전트의 역할**: 분석 요청(GitHub Issue)을 받아 dbt 실행, BigQuery 쿼리, marimo 리포트 생성을 자동화합니다.
```

**섹션 2: 도메인 정의 (Domain Definitions)**

에이전트가 잘못 해석할 수 있는 비즈니스 용어를 정확히 정의합니다.

```markdown
## 도메인 정의

### 활성 사용자 (Active User)
- **DAU**: 해당 날짜에 `event_type IN ('app_open', 'purchase', 'search')` 중 하나 이상 발생시킨 사용자
- **MAU**: 해당 월(calendar month)에 위 조건을 만족하는 날이 1일 이상인 사용자
- ⚠️ '활성'을 단순 앱 설치나 push 알림 수신으로 정의하지 말 것

### 날짜 처리 기준
- 모든 타임스탬프는 UTC → KST(+9) 변환 후 사용
- 분석 기간의 기본값: 최근 30일 (오늘 제외)
```

**섹션 3: 아키텍처 규약 (Architecture Conventions)**

에이전트가 파일을 생성하거나 쿼리를 작성할 때 따라야 할 패턴을 지정합니다.

```markdown
## 아키텍처 규약

### dbt 계층 접근 원칙
- 에이전트는 분석 쿼리에서 `raw_*` 테이블을 직접 참조하지 않는다
- `stg_*` 모델은 단순 정제만 포함, 비즈니스 로직은 `fct_*`에서 처리
- 새 분석 지표는 반드시 mart 모델로 추가한다 (임시 쿼리 금지)

### BigQuery 비용 관리 (on-demand 가격 기준)
- 모든 쿼리는 실행 전 dry-run으로 비용 추정 (1TB 스캔 = $5 USD)
- 파티션 필터 없는 `raw_events` 전체 스캔 절대 금지 (예상 비용: ~$2.50/회)
- 단일 분석 작업의 쿼리 비용 한도: $1.00 USD (약 200GB 스캔)
```

**섹션 4: 에이전트 행동 정책 (Agent Behavior Policy)**

에이전트가 모호한 상황에서 따라야 할 의사결정 규칙입니다.

```markdown
## 에이전트 행동 정책

### 불확실성 처리
- 분석 범위가 불명확하면 작업을 시작하지 말고 먼저 GitHub Issue에 질문을 남긴다
- 두 가지 방법론이 가능할 때 더 보수적인 방법을 선택한다

### 실패 처리
- dbt 테스트 실패 시: 자동 수정하지 말고 실패 원인과 영향 범위를 Issue에 보고
- BigQuery 쿼리 오류 시: 에러 메시지 전체를 기록하고 재시도 횟수는 2회로 제한
- 예상 비용 초과 시: 반드시 사람에게 승인을 요청하고 작업을 일시 중단
```

**섹션 5: 파일 위치 지도 (File Map)**

에이전트가 파일을 생성하거나 수정할 때 어디에 저장해야 하는지 알 수 있도록 합니다.

```markdown
## 파일 위치 지도

| 파일 유형 | 저장 위치 | 명명 규칙 |
|-----------|-----------|-----------|
| dbt 소스 정의 | `models/staging/sources.yml` | — |
| dbt 스테이징 모델 | `models/staging/stg_*.sql` | `stg_` 접두사 필수 |
| dbt 마트 모델 | `models/marts/fct_*.sql` | `fct_` 접두사 필수 |
| marimo 노트북 | `notebooks/` | `analysis_YYYYMMDD_topic.py` |
| 완료 증거 | `evidence/YYYYMMDD/` | 날짜 폴더별 구분 |
| 임시 쿼리 | 절대 저장하지 않음 | — |
```

**관찰 질문 3**: 스타터 레포의 AGENTS.md에 위 5개 섹션이 모두 있는가? 없다면 어떤 섹션이 빠져 있는가?

**관찰 질문 4**: "에이전트 행동 정책"에서 dbt 테스트 실패 시 자동 수정을 금지하는 이유는 무엇인가?

### 관찰 1-C: 슬래시 커맨드 구조 분석

```bash
# 스타터 레포의 슬래시 커맨드 파일 읽기
ls .claude/commands/
cat .claude/commands/analyze-dau.md
```

**슬래시 커맨드(slash command)**란 Claude Code에서 `/커맨드이름` 형태로 실행하는, 미리 정의된 작업 명세입니다. `.claude/commands/` 폴더에 Markdown 파일로 저장되며, 파일 이름이 곧 커맨드 이름이 됩니다.

```
.claude/commands/
├── analyze-dau.md        → /analyze-dau 로 실행
├── run-dbt-pipeline.md   → /run-dbt-pipeline 로 실행
└── generate-report.md    → /generate-report 로 실행
```

**슬래시 커맨드 vs 자유 형식 프롬프트 비교**:

| 기준 | 자유 형식 프롬프트 | 슬래시 커맨드 |
|------|-------------------|---------------|
| 일관성 | 매번 다른 해석 가능 | 동일 절차 보장 |
| 재사용성 | 매번 다시 작성 | 한 번 정의, 반복 실행 |
| 파라미터 처리 | 에이전트가 유추 | 명시적 파라미터 전달 |
| 검증 | 어려움 | 입력 유효성 검사 포함 가능 |
| 팀 공유 | 개인 경험에 의존 | Git 버전 관리로 팀 공유 |

### 관찰 1-D: 슬래시 커맨드 파일의 표준 섹션 구조

```bash
# 스타터 레포의 analyze-dau.md 전체 읽기
cat .claude/commands/analyze-dau.md
```

효과적인 커맨드 파일은 다음 섹션으로 구성됩니다. 스타터 레포 파일에서 각 섹션을 찾아 확인합니다:

```markdown
# /커맨드이름

## 목적 (Purpose)
이 커맨드가 무엇을 하는지 한 문장으로 설명합니다.

## 파라미터 (Parameters)
- `PARAM_NAME` (필수/선택): 설명, 예시값, 기본값

## 전제 조건 (Preconditions)
실행 전 만족해야 하는 조건 목록

## 절차 (Steps)
에이전트가 따라야 할 단계별 지침

## 출력 명세 (Output Specification)
커맨드 실행 후 생성되어야 하는 파일, 메시지, 상태 변화

## 완료 기준 (Completion Criteria)
이 커맨드가 "성공적으로 완료"되었다고 판단하는 기계적 기준

## 오류 처리 (Error Handling)
예상 가능한 실패 상황과 대응 방법

## 예상 비용 (Expected Cost)
BigQuery on-demand 기준 예상 스캔량과 비용 ($5/TB)
```

**$ARGUMENTS 플레이스홀더**:

커맨드 파일 안에서 `$ARGUMENTS`를 사용하면 실행 시 전달된 인자로 자동 치환됩니다:

```
/analyze-dau start_date=2024-01-01 end_date=2024-01-31 segment=all
```

커맨드 파일 내부:
```markdown
## 절차

1. 다음 파라미터로 분석을 시작하세요: $ARGUMENTS
2. 파라미터가 없으면 기본값 적용: start_date=최근 30일, end_date=어제
```

**관찰 질문 5**: 스타터 레포의 `analyze-dau.md`에서 "완료 기준" 섹션을 찾으라. PASS 조건이 몇 개 정의되어 있는가?

**관찰 질문 6**: `analyze-dau.md`에서 예상 비용이 명시되어 있는가? BigQuery on-demand 가격($5/TB)을 기준으로 한 계산이 포함되어 있는가?

### 관찰 1-E: 재사용 가능한 분석 커맨드 설계 원칙

스타터 레포의 커맨드 파일들을 읽으며 다음 5가지 설계 원칙이 어떻게 적용되었는지 확인합니다.

**원칙 1: 단일 책임 (Single Responsibility)**

각 커맨드는 하나의 명확한 목적만 가져야 합니다.

❌ 나쁜 설계: `/full-analysis` — "dbt 실행하고, BigQuery 쿼리하고, 리포트 만들고, 이슈 닫아"
✅ 좋은 설계:
- `/run-dbt-pipeline` — dbt 실행과 테스트
- `/query-dau-metrics` — BigQuery 집계 쿼리
- `/generate-report` — marimo 노트북 실행 및 리포트 생성

**원칙 2: 명시적 입력과 출력**

에이전트가 결과를 어디에 저장해야 할지 추측하지 않도록, 출력 경로를 명시합니다.

```markdown
## 출력 명세

- **dbt 실행 결과**: `evidence/YYYYMMDD/dbt_results.json`
  - 형식: dbt의 `run_results.json` 파일 복사본
  - 반드시 포함할 필드: `status`, `execution_time`, `failures`
- **비용 기록**: `evidence/YYYYMMDD/query_costs.json`
  - 형식: `{"query_id": "...", "bytes_processed": ..., "estimated_cost_usd": ...}`
```

**원칙 3: 비용 인식 설계 (Cost-Aware Design)**

BigQuery on-demand 가격 기반 환경에서 모든 커맨드는 비용을 명시해야 합니다.

```markdown
## 예상 비용

| 쿼리 | 예상 스캔 | 예상 비용 (on-demand) |
|------|-----------|----------------------|
| DAU 집계 (30일, fct 테이블) | ~5GB | ~$0.025 |
| MAU 집계 (1개월, fct 테이블) | ~8GB | ~$0.040 |
| raw_events 전체 스캔 (금지) | ~500GB | ~$2.50 |

> BigQuery on-demand 가격: $5.00 USD / TB 스캔
```

**원칙 4: 실패 안전 (Fail-Safe) 기본값**

커맨드의 기본 동작은 가장 안전한 선택이어야 합니다.

```markdown
## 기본값 정책

- `start_date` 미지정: 오늘 기준 31일 전 (어제를 포함하는 30일)
- `end_date` 미지정: 어제 날짜 (오늘 데이터는 미완성일 수 있으므로 제외)
- `dry_run` 미지정: `true` (처음 실행 시 dry-run 강제)
```

**원칙 5: 검증 가능한 완료 기준**

```markdown
## 완료 기준 (Pass/Fail)

다음 조건이 **모두** 참이어야 커맨드가 성공적으로 완료된 것으로 판단합니다:

✅ PASS: `evidence/YYYYMMDD/dbt_results.json` 파일이 존재하고 `"status": "success"` 포함
✅ PASS: `evidence/YYYYMMDD/query_costs.json` 파일이 존재하고 `estimated_cost_usd < 1.0`
✅ PASS: dbt 테스트 결과에서 `failures` 카운트가 0
❌ FAIL: 위 조건 중 하나라도 충족되지 않으면 작업 실패로 보고
```

**관찰 요약**: 이제 다음을 이해했어야 합니다.
- AGENTS.md의 5개 섹션 구조와 각 섹션의 역할
- 슬래시 커맨드 파일의 표준 섹션 구조
- 재사용 가능한 분석 커맨드의 5가지 설계 원칙
- 왜 자유 형식 프롬프트보다 슬래시 커맨드가 일관성 면에서 우수한가

---

## 2단계: 수정 — 기존 커맨드와 AGENTS.md 조정하기

> **목표**: 스타터 레포의 기존 AGENTS.md와 DAU 커맨드를 분석하여 부족한 부분을 찾고, 프로젝트 요구사항에 맞게 개선합니다.

### 수정 2-A: AGENTS.md에 누락된 도메인 정의 추가

스타터 레포의 AGENTS.md에 Stickiness 지표 정의가 빠져 있다면 추가합니다.

**현재 상태 확인**:
```bash
# AGENTS.md에서 Stickiness 정의 검색
grep -n "stickiness\|Stickiness\|끈적\|끈끈" AGENTS.md || echo "Stickiness 정의 없음"
```

**수정**: `## 도메인 정의` 섹션에 추가

```markdown
### Stickiness (사용자 고착도)
- **정의**: DAU ÷ MAU × 100 (%)
- **계산 주기**: 월 단위로 계산, 해당 월의 평균 DAU 사용
- **참고 값**: 업계 평균 20~30%, 우리 서비스 목표 25% 이상
- ⚠️ DAU와 MAU가 다른 날짜 범위에서 계산되지 않도록 주의 (같은 월 기준)
```

**수정 후 확인**:
```bash
# 추가된 정의 확인
grep -A 5 "Stickiness" AGENTS.md
```

### 수정 2-B: 비용 기준 구체화

스타터 레포의 AGENTS.md 비용 정책에 3단계 에스컬레이션 기준이 없다면 추가합니다.

**수정**: 기존 `### BigQuery 비용 관리` 섹션 개선

기존 텍스트:
```markdown
### BigQuery 비용 관리
- 모든 쿼리는 실행 전 dry-run으로 비용 추정
- 파티션 필터 없는 raw_events 전체 스캔 절대 금지
```

수정 후:
```markdown
### BigQuery 비용 관리 (on-demand 가격: $5.00 USD / TB 스캔)

| 단계 | 쿼리 예상 비용 | 에이전트 행동 |
|------|---------------|---------------|
| 자동 실행 허용 | $0.10 미만 (~20GB) | 바로 실행 후 비용 기록 |
| 실행 + 기록 | $0.10 ~ $1.00 | 실행하되 Issue에 비용 코멘트 |
| 사람 승인 필요 | $1.00 초과 | 즉시 중단, Issue에 승인 요청 |

**금지 쿼리 패턴** (모두 훅으로도 차단됨):
- `FROM raw_events` 파티션 필터 없이 → 전체 스캔 ~$2.50
- `SELECT *` 광범위 스캔 → 필요한 컬럼만 명시할 것
```

### 수정 2-C: 슬래시 커맨드 파라미터 기본값 강화

스타터 레포의 `analyze-dau.md`를 읽고, `dry_run` 기본값이 명시되어 있는지 확인하고 추가합니다.

**현재 파라미터 확인**:
```bash
grep -A 20 "## 파라미터" .claude/commands/analyze-dau.md
```

**수정**: `dry_run` 파라미터와 기본값 추가

```markdown
## 파라미터

- `start_date` (선택, 기본값: 31일 전): 분석 시작일, 형식 YYYY-MM-DD
- `end_date` (선택, 기본값: 어제): 분석 종료일, 형식 YYYY-MM-DD
- `segment` (선택, 기본값: "all"): 사용자 세그먼트 필터
  - 허용값: "all", "new_users", "returning_users"
- `dry_run` (선택, 기본값: true): 첫 실행 시 dry-run으로 비용만 확인

**안전 규칙**: `dry_run=false`를 명시적으로 지정하지 않으면 항상 dry-run 먼저 실행합니다.
이유: 날짜 범위 실수로 인한 의도치 않은 대용량 스캔을 방지합니다.

**인자 예시**: $ARGUMENTS
```

### 수정 2-D: 완료 기준 FAIL 처리 로직 구체화

스타터 레포의 완료 기준에 FAIL 시 처리 방법이 없다면 추가합니다.

**수정**: 기존 완료 기준 섹션 개선

```markdown
## 완료 기준 (Pass/Fail)

| 기준 | PASS 조건 | FAIL 시 처리 |
|------|-----------|-------------|
| 결과 파일 존재 | `evidence/YYYYMMDD/dau_results.json` 존재 | 에러 메시지 출력 후 종료 |
| 비용 기록 존재 | `evidence/YYYYMMDD/query_costs.json` 존재 | 경고 후 계속 |
| 비용 한도 준수 | `estimated_cost_usd < 1.0` | 초과 금액 보고 후 종료, 사람 승인 대기 |
| 결과 행 수 | 결과가 1행 이상 | "데이터 없음" 보고 후 종료 |
| dbt 테스트 통과 | fct 모델 테스트 failures = 0 | 테스트 실패 목록을 Issue에 보고 후 중단 |
```

**수정 요약**: 이 단계에서 변경한 항목들:
1. AGENTS.md: Stickiness 도메인 정의 추가
2. AGENTS.md: BigQuery 비용 에스컬레이션 3단계 기준 추가
3. `analyze-dau.md`: `dry_run` 파라미터 기본값 명시
4. `analyze-dau.md`: FAIL 시 처리 방법 구체화

---

## 3단계: 창작 — 나만의 커맨드와 AGENTS.md 작성

> **목표**: DAU 커맨드를 참고하여 MAU 슬래시 커맨드를 처음부터 작성하고, 완성된 AGENTS.md를 직접 구성합니다.

### 창작 3-A: MAU 분석 슬래시 커맨드 작성

**목표**: `.claude/commands/analyze-mau.md` 파일을 처음부터 작성합니다. `analyze-dau.md`의 구조를 참고하되, MAU 특유의 차이점을 반영합니다.

**DAU 커맨드와의 핵심 차이점**:

| 구분 | DAU 커맨드 | MAU 커맨드 |
|------|------------|------------|
| 시간 단위 | 일(day) | 월(month) |
| 파라미터 | `start_date`, `end_date` | `year_month` (YYYY-MM) |
| dbt 모델 | `fct_daily_active_users` | `fct_monthly_active_users` |
| 예상 스캔량 | ~5GB (30일) | ~8GB (1개월) |
| 부가 지표 | DAU만 | MAU + Stickiness (DAU/MAU) |

**`.claude/commands/analyze-mau.md` 전체 작성**:

```bash
# commands 디렉토리 생성 (아직 없다면)
mkdir -p .claude/commands
```

```markdown
# /analyze-mau

<!-- 목적: 지정된 달의 MAU와 Stickiness(DAU/MAU 비율)를 계산합니다.
     하니스 역할: 에이전트가 AGENTS.md의 MAU 정의를 자동으로 참조하게 합니다.
     비용 참고: fct_monthly_active_users + fct_daily_active_users 조인 ≈ $0.065 USD -->

## 목적

지정된 달의 월간 활성 사용자(MAU)와 Stickiness(DAU/MAU 비율)를 계산하고,
BigQuery 쿼리 결과와 비용 기록을 `evidence/` 폴더에 저장합니다.

## 파라미터

- `year_month` (필수): 분석 대상 월, 형식 YYYY-MM (예: 2024-01)
- `compare_prev_month` (선택, 기본값: true): 전월 비교 포함 여부
- `dry_run` (선택, 기본값: true): 실행 전 dry-run으로 비용만 확인

**인자 예시**: $ARGUMENTS

**안전 규칙**: `dry_run=false`를 명시적으로 지정하지 않으면 항상 dry-run 먼저 실행합니다.

## 전제 조건

다음을 확인한 후 작업을 시작하세요:

1. `dbt run --select fct_monthly_active_users fct_daily_active_users` 가 성공했는지 확인
2. `year_month` 형식이 YYYY-MM 인지 확인 (예: 2024-01 ✅, 2024-1 ❌)
3. 해당 월의 데이터가 BigQuery에 존재하는지 확인
4. `evidence/` 폴더가 없으면 생성

## 예상 비용

| 쿼리 | 예상 스캔량 | 예상 비용 (on-demand $5/TB) |
|------|------------|---------------------------|
| MAU 집계 (1개월, fct 테이블) | ~8GB | ~$0.040 |
| Stickiness 계산 (DAU/MAU 조인) | ~5GB | ~$0.025 |
| **합계** | ~13GB | **~$0.065** |

> raw_events 전체 스캔 시 예상 비용: ~$2.50 (fct 모델 사용으로 50배 절감)

## 절차

### 1단계: 비용 사전 검사 (dry-run)

다음 쿼리를 `--dry_run` 플래그로 먼저 실행합니다:

```sql
-- MAU 집계 쿼리 (교육 목적: fct 모델 사용으로 raw 스캔 방지)
-- 예상 비용: ~$0.040 USD (fct_monthly_active_users, 월 단위, 파티션 필터)
SELECT
  DATE_TRUNC(event_date, MONTH) AS month,     -- 월 단위 집계
  COUNT(DISTINCT user_id) AS mau               -- AGENTS.md 활성 사용자 정의 기준
FROM `{project_id}.analytics.fct_monthly_active_users`
WHERE DATE_TRUNC(event_date, MONTH) = DATE('{year_month}-01')  -- 파티션 필터
GROUP BY 1
```

- 예상 스캔량이 **25GB 초과** 시 작업을 중단하고 사용자에게 보고합니다.
- 예상 비용이 **$0.13 USD 초과** 시 실행 전 확인 메시지를 출력합니다.

### 2단계: 실제 MAU 쿼리 실행

dry-run 통과 후 MAU를 계산합니다:

```bash
RESULT_DIR="evidence/$(date +%Y%m%d)"
mkdir -p "$RESULT_DIR"

bq query \
  --format=json \
  --nouse_legacy_sql \
  "SELECT ..." > "$RESULT_DIR/mau_results.json"
```

### 3단계: Stickiness 계산

MAU 결과를 얻은 후 평균 DAU와 조인하여 Stickiness를 계산합니다:

```sql
-- Stickiness = 평균 DAU / MAU × 100
-- 교육 목적: 두 fct 모델을 조인하여 파생 지표 계산
-- 예상 추가 비용: ~$0.025 USD
SELECT
  '{year_month}' AS month,
  mau.mau,
  avg_dau.avg_dau,
  ROUND(avg_dau.avg_dau / mau.mau * 100, 1) AS stickiness_pct
FROM (
  SELECT COUNT(DISTINCT user_id) AS mau
  FROM `{project_id}.analytics.fct_monthly_active_users`
  WHERE DATE_TRUNC(event_date, MONTH) = DATE('{year_month}-01')
) mau
CROSS JOIN (
  SELECT AVG(dau) AS avg_dau
  FROM (
    SELECT event_date, COUNT(DISTINCT user_id) AS dau
    FROM `{project_id}.analytics.fct_daily_active_users`
    WHERE DATE_TRUNC(event_date, MONTH) = DATE('{year_month}-01')
    GROUP BY 1
  )
) avg_dau
```

### 4단계: 전월 비교 (compare_prev_month=true일 때)

```bash
# 전월 계산 (YYYY-MM 형식에서 1달 빼기)
PREV_MONTH=$(date -d "${year_month}-01 -1 month" +%Y-%m 2>/dev/null \
  || python3 -c "
from datetime import date
y, m = map(int, '${year_month}'.split('-'))
pm = date(y, m, 1).replace(month=m-1 if m > 1 else 12, year=y if m > 1 else y-1)
print(pm.strftime('%Y-%m'))
")
```

### 5단계: 비용 기록 및 완료 보고

```bash
# 비용 기록 파일 생성
cat > "$RESULT_DIR/query_costs_mau.json" << EOF
{
  "command": "analyze-mau",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "year_month": "${year_month}",
  "bytes_processed": ACTUAL_BYTES,
  "estimated_cost_usd": ACTUAL_COST
}
EOF
```

완료 요약 형식:
```
MAU 분석 완료 — {year_month}
- MAU: XXX명
- 전월 대비: +X.X% (or -X.X%)
- Stickiness: XX.X%
- 쿼리 비용: $X.XX USD (XX GB 스캔)
- 결과 파일: evidence/YYYYMMDD/mau_results.json
```

## 완료 기준 (Pass/Fail)

| 기준 | PASS 조건 | FAIL 시 처리 |
|------|-----------|-------------|
| MAU 결과 파일 | `evidence/YYYYMMDD/mau_results.json` 존재 | 에러 메시지 후 종료 |
| Stickiness 범위 | `stickiness_pct` 값이 0~100 사이 | 이상값 경고 후 Issue 코멘트 |
| 비용 한도 준수 | `estimated_cost_usd < 0.20` | 초과 금액 보고 후 중단 |
| 전월 비교 포함 | `compare_prev_month=true`일 때 prev_month 데이터 포함 | 경고 후 계속 |
| 비용 기록 파일 | `evidence/YYYYMMDD/query_costs_mau.json` 존재 | 경고 후 계속 |

## 오류 처리

| 오류 상황 | 대응 방법 |
|-----------|-----------|
| BigQuery 인증 실패 | "GCP 서비스 계정 인증을 확인하세요" 메시지 출력 |
| fct 테이블 미존재 | "`dbt run --select fct_monthly_active_users`를 먼저 실행하세요" |
| year_month 형식 오류 | "날짜 형식은 YYYY-MM이어야 합니다 (예: 2024-01)" |
| 해당 월 데이터 없음 | "데이터가 없습니다. 날짜 범위를 확인하세요" |
| 비용 한도 초과 | 예상 비용과 스캔량 출력 후 사용자 승인 대기 |
| Stickiness 100% 초과 | "DAU > MAU는 계산 오류입니다. fct 모델 데이터를 확인하세요" |
```

**검증**:
```bash
# 커맨드 파일 생성 확인
test -f .claude/commands/analyze-mau.md && echo "✅ analyze-mau.md 생성됨" || echo "❌ 파일 없음"

# Claude Code 세션에서 커맨드 실행 테스트
# /analyze-mau year_month=2024-01
```

### 창작 3-B: 완성된 AGENTS.md 작성

**목표**: 레포 루트에 5개 섹션이 모두 포함된 완성된 `AGENTS.md`를 작성합니다.

**작성 순서**:
1. 먼저 기존 AGENTS.md를 읽어 보존할 내용 파악
2. 빠진 섹션을 추가하거나 부족한 섹션을 강화
3. 에이전트 관점의 작성 원칙 적용

**완성된 AGENTS.md 예시** (이 구조를 기반으로 직접 작성하세요):

```markdown
# AGENTS.md — 에이전트 운영 가이드

> 이 파일은 Claude Code 에이전트가 이 레포지토리에서 작업할 때 참조하는 맥락 문서입니다.
> README.md와 다르게, 이 문서는 에이전트의 행동을 안내하는 목적으로 작성됩니다.

## 프로젝트 개요

이 레포는 B2C 모바일 앱의 DAU/MAU 분석 파이프라인을 관리합니다.

**데이터 흐름**:
```
BigQuery raw_events
    → dbt stg_events (정제·표준화)
    → dbt fct_daily_active_users (DAU 집계)
    → dbt fct_monthly_active_users (MAU 집계)
    → marimo 분석 노트북
    → HTML 리포트 (evidence/ 폴더)
```

**에이전트의 역할**: GitHub Issue로 들어오는 분석 요청을 받아 dbt 파이프라인 실행,
BigQuery 쿼리, marimo 리포트 생성을 자동화합니다.

## 도메인 정의

에이전트는 다음 정의를 정확히 사용해야 합니다. 임의로 다르게 해석하지 마세요.

### 활성 사용자 (Active User)
- **DAU**: 해당 날짜에 `event_type IN ('app_open', 'purchase', 'search')` 이벤트를 1회 이상 발생시킨 사용자
- **MAU**: 해당 월(calendar month)에 위 조건을 만족하는 날이 1일 이상인 사용자
- ⚠️ '활성'을 단순 앱 설치(install), push 알림 수신, 또는 세션 시작으로 정의하지 말 것

### Stickiness (사용자 고착도)
- **정의**: 평균 DAU ÷ MAU × 100 (%)
- **계산**: 해당 월의 일별 DAU 평균값을 사용, MAU와 같은 월 기준
- ⚠️ DAU와 MAU가 다른 날짜 범위에서 계산되지 않도록 주의

### 날짜 처리 기준
- 모든 이벤트 타임스탬프는 UTC → KST(+9시간) 변환 후 사용
- 분석 기간 기본값: 최근 30일 (오늘 제외 — 당일 데이터는 미완성)
- 날짜 형식: YYYY-MM-DD (BigQuery 파티션 기준)

## 아키텍처 규약

### dbt 계층 접근 원칙

에이전트는 항상 다음 계층 순서로 데이터를 접근합니다:

```
❌ 금지: raw_events 직접 쿼리 (전체 스캔 ~$2.50/회)
✅ 허용: stg_events (파티션 필터 필수)
✅ 권장: fct_daily_active_users, fct_monthly_active_users (사전 집계, 저비용)
```

- `stg_*` 모델: 단순 정제·표준화만 포함, 비즈니스 로직 없음
- `fct_*` 모델: 집계 지표 포함, 분석 쿼리는 여기서 시작
- 새 지표: 반드시 mart 모델로 추가 (임시 쿼리 파일 생성 금지)

### BigQuery 비용 관리 (on-demand: $5.00 USD / TB 스캔)

| 예상 비용 | 에이전트 행동 |
|-----------|--------------|
| $0.10 미만 (~20GB) | 자동 실행 후 비용 기록 |
| $0.10 ~ $1.00 | 실행하되 Issue에 비용 코멘트 추가 |
| $1.00 초과 | 즉시 중단, Issue에 승인 요청 후 대기 |

**모든 쿼리 실행 전 dry-run 의무**: `bq query --dry_run`으로 먼저 스캔 바이트 확인

## 에이전트 행동 정책

### 불확실성 처리
- 분석 범위가 불명확하면 작업 시작 전 GitHub Issue에 질문 남기기
- 두 가지 방법론이 가능할 때 더 보수적인(저비용, 낮은 리스크) 방법 선택

### 실패 처리
- **dbt 테스트 실패**: 자동 수정 금지. 실패 원인·영향 범위를 Issue에 보고 후 중단
- **BigQuery 오류**: 에러 메시지 전체 기록, 최대 2회 재시도 후 사람에게 보고
- **비용 한도 초과**: 즉시 중단, 예상 비용과 사유를 Issue에 코멘트

### 완료 기준
모든 분석 작업은 다음 증거 파일을 `evidence/YYYYMMDD/` 폴더에 남겨야 합니다:
- `dbt_results.json`: dbt run/test 결과 (status, failures 포함)
- `query_costs.json`: 실행한 BigQuery 쿼리 비용 기록
- 리포트 파일: marimo HTML 리포트 경로

## 파일 위치 지도

| 파일 유형 | 저장 위치 | 명명 규칙 |
|-----------|-----------|-----------|
| dbt 소스 정의 | `models/staging/sources.yml` | — |
| dbt 스테이징 모델 | `models/staging/stg_*.sql` | `stg_` 접두사 필수 |
| dbt 마트 모델 | `models/marts/fct_*.sql` | `fct_` 접두사 필수 |
| marimo 노트북 | `notebooks/` | `analysis_YYYYMMDD_topic.py` |
| 완료 증거 | `evidence/YYYYMMDD/` | 날짜별 폴더 |
| 비용 기록 | `evidence/YYYYMMDD/query_costs.json` | 날짜별 폴더 |
| 임시 쿼리 파일 | **절대 저장하지 않음** | — |
```

**AGENTS.md 작성 원칙 (피해야 할 안티패턴)**:

| 안티패턴 | 문제 | 올바른 방법 |
|----------|------|-------------|
| "일반적인 star schema를 따릅니다" | 에이전트가 다르게 해석할 여지 | 구체적인 테이블명과 관계 명시 |
| "raw_events를 쿼리하지 마세요" | 대안 없이 금지만 | "대신 fct_* 사용, 이유는..." |
| "쿼리 비용에 주의하세요" | 기준이 모호 | 숫자로 명시: "$1.00 초과 시 중단" |
| "최선을 다해 분석해줘" | 에이전트가 임의 해석 | 구체적 지표·방법론·출력 형식 명시 |

### 창작 3-C: DAU 커맨드 종단 테스트

완성된 AGENTS.md와 커맨드 파일들이 제대로 동작하는지 확인합니다.

```bash
# 1. 파일 존재 확인
for f in "AGENTS.md" ".claude/commands/analyze-dau.md" ".claude/commands/analyze-mau.md"; do
    test -f "$f" && echo "✅ $f" || echo "❌ $f 없음"
done

# 2. AGENTS.md 품질 검사
echo "--- AGENTS.md 품질 검사 ---"
grep -q "활성 사용자" AGENTS.md && echo "✅ 활성 사용자 정의 존재" || echo "❌ 활성 사용자 정의 없음"
grep -q "Stickiness" AGENTS.md && echo "✅ Stickiness 정의 존재" || echo "❌ Stickiness 정의 없음"
grep -q '\$5' AGENTS.md && echo "✅ BigQuery 비용 기준 존재" || echo "❌ 비용 기준 없음"
grep -q "evidence/" AGENTS.md && echo "✅ 증거 파일 위치 명시" || echo "❌ 증거 파일 위치 없음"

# 3. 슬래시 커맨드 품질 검사
echo "--- 커맨드 품질 검사 ---"
grep -q "PASS" .claude/commands/analyze-dau.md && echo "✅ DAU 완료 기준 존재" || echo "❌ DAU 완료 기준 없음"
grep -q "PASS" .claude/commands/analyze-mau.md && echo "✅ MAU 완료 기준 존재" || echo "❌ MAU 완료 기준 없음"
grep -q "dry_run" .claude/commands/analyze-dau.md && echo "✅ DAU dry-run 명시" || echo "❌ DAU dry-run 없음"
grep -q "\$0\." .claude/commands/analyze-mau.md && echo "✅ MAU 비용 추정 존재" || echo "❌ MAU 비용 없음"
```

### 창작 3-D: Claude Code 세션에서 동작 확인

```bash
# Claude Code 세션에서 직접 실행하여 확인

# 테스트 1: AGENTS.md 로딩 확인
# claude 세션: "이 프로젝트에서 활성 사용자를 어떻게 정의하나요?"
# 기대 응답: AGENTS.md에 정의된 event_type 기반 정의 인용

# 테스트 2: DAU 커맨드 실행
# claude 세션: /analyze-dau start_date=2024-01-01 end_date=2024-01-07
# 기대 결과: dry-run 먼저 실행, 비용 추정 출력, 실제 쿼리 실행

# 테스트 3: MAU 커맨드 실행
# claude 세션: /analyze-mau year_month=2024-01
# 기대 결과: MAU + Stickiness 계산, evidence/ 폴더에 결과 파일 생성
```

---

## 6. 프롬프트 엔지니어링 패턴

경력 데이터 분석가가 슬래시 커맨드를 작성할 때 적용할 수 있는 핵심 패턴입니다.

### 패턴 1: 역할 고정 (Role Anchoring)

커맨드 파일 상단에 에이전트의 역할을 명확히 지정합니다.

```markdown
<!-- 역할: 이 커맨드를 실행하는 에이전트는
     "BigQuery 비용에 민감한 데이터 엔지니어"로서 행동합니다.
     모든 쿼리는 최소 비용 원칙으로 설계해야 합니다. -->
```

### 패턴 2: 체인-오브-소트 강제 (Forced Chain-of-Thought)

에이전트가 결론으로 바로 뛰어들지 않도록, 중간 확인 단계를 명시합니다.

```markdown
## 절차

1. 먼저 fct_daily_active_users 테이블의 최신 갱신 날짜를 확인하세요
2. 요청된 start_date가 테이블 커버리지 범위 내인지 확인하세요
3. 비용을 dry-run으로 추정하세요
4. (이 세 가지를 확인한 후에만) 실제 쿼리를 실행하세요
```

### 패턴 3: 형식 고정 (Output Format Locking)

결과의 형식을 JSON 스키마로 명시하면 파싱이 용이하고 검증이 가능합니다.

```markdown
## 출력 형식

결과 파일은 반드시 다음 JSON 스키마를 따라야 합니다:

```json
{
  "analysis_type": "dau",
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "summary": {"avg_dau": 0, "peak_dau": 0, "peak_date": "YYYY-MM-DD"},
  "cost": {"bytes_processed": 0, "estimated_usd": 0.0},
  "rows": [{"event_date": "YYYY-MM-DD", "dau": 0}]
}
```
```

### 패턴 4: 비용 인식 주석 (Cost-Aware Annotation)

쿼리마다 예상 비용을 인라인 주석으로 포함합니다.

```sql
-- 예상 비용: ~$0.025 USD (fct 테이블, 30일 범위, 파티션 필터 적용)
-- dry-run 필수: 실행 전 반드시 --dry_run 플래그로 비용 확인
SELECT
  event_date,
  COUNT(DISTINCT user_id) AS dau
FROM `{project_id}.analytics.fct_daily_active_users`
WHERE event_date BETWEEN '{start_date}' AND '{end_date}'  -- 파티션 필터 필수
GROUP BY 1
ORDER BY 1
```

### 패턴 5: 에스컬레이션 트리거 (Escalation Trigger)

에이전트가 스스로 처리할 수 없는 상황에서 사람에게 보고하도록 명시합니다.

```markdown
## 에스컬레이션 기준

다음 상황에서는 작업을 **즉시 중단**하고 GitHub Issue에 코멘트를 남긴 후 사람의 응답을 기다립니다:
- 예상 비용이 $1.00 USD를 초과할 때
- dbt 테스트가 2개 이상 실패할 때
- 쿼리 결과가 이전 달 대비 50% 이상 변동할 때 (데이터 이상 가능성)
- 에러가 2회 재시도 후에도 해결되지 않을 때
```

### 피해야 할 안티패턴

| 안티패턴 | 문제 | 해결 방법 |
|----------|------|-----------|
| "최선을 다해 분석해줘" | 에이전트가 임의로 해석 | 구체적인 지표와 방법론 명시 |
| 파라미터 기본값 생략 | 에이전트가 추측하거나 오류 발생 | 모든 선택 파라미터에 기본값 명시 |
| 출력 형식 미지정 | 매번 다른 구조의 결과 파일 생성 | JSON 스키마 또는 파일명 패턴 고정 |
| 완료 기준 부재 | 에이전트가 임의로 "완료" 선언 | Pass/Fail 기준 명시 |
| 비용 언급 없음 | 비용 초과 쿼리 자동 실행 | 예상 비용과 한도 명시 |

---

## 7. 모듈 자기 점검 체크리스트

모듈 2를 완료했다면 다음 항목을 직접 실행하여 PASS/FAIL을 확인하세요.

### 관찰 단계 이해 체크리스트

- [ ] **AGENTS.md vs README.md 차이**: AGENTS.md가 에이전트 관점에서 작성된 이유를 설명할 수 있다
  - ✅ 합격: "AGENTS.md는 에이전트가 레포에서 올바르게 일하도록 맥락을 제공, README는 인간용"
  - ❌ 불합격: 두 파일의 차이를 설명 못 함

- [ ] **슬래시 커맨드 이점**: 자유 형식 프롬프트보다 슬래시 커맨드를 사용하는 구체적 이점 3가지 설명 가능
  - ✅ 합격: "일관성, 재사용성, 팀 공유 (또는 검증 가능성, 파라미터 명시성)"
  - ❌ 불합격: 1~2가지만 말할 수 있음

- [ ] **완료 기준 중요성**: 슬래시 커맨드의 완료 기준이 없을 때 어떤 문제가 발생하는지 설명 가능
  - ✅ 합격: "에이전트가 임의로 '완료'를 선언하고 실제로 파일이 생성되지 않았어도 모름"
  - ❌ 불합격: 모름

### 수정 단계 구현 체크리스트

- [ ] **AGENTS.md 수정**: Stickiness 정의, 3단계 비용 기준이 추가되었다
  - ✅ 합격: `grep "Stickiness\|0\.10" AGENTS.md`가 결과를 반환
  - ❌ 불합격: 수정 안 함

- [ ] **dry_run 파라미터 추가**: `analyze-dau.md`에 `dry_run` 기본값이 명시되었다
  - ✅ 합격: `grep "dry_run" .claude/commands/analyze-dau.md`가 결과를 반환
  - ❌ 불합격: dry_run 파라미터 없음

### 창작 단계 구현 체크리스트

```bash
# 파일 존재 여부 일괄 확인
for f in \
  "AGENTS.md" \
  ".claude/commands/analyze-dau.md" \
  ".claude/commands/analyze-mau.md"; do
  test -f "$f" && echo "✅ PASS: $f" || echo "❌ FAIL: $f 없음"
done
```

| 점검 항목 | 확인 방법 | 합격 기준 |
|-----------|-----------|-----------|
| 활성 사용자 정의 | AGENTS.md에서 "활성 사용자" 검색 | event_type 기반 정의 포함 |
| BigQuery 비용 한도 | AGENTS.md에서 "$" 검색 | USD 숫자가 명시됨 |
| 파일 위치 지도 | AGENTS.md에서 "evidence/" 검색 | 완료 증거 경로 포함 |
| DAU 커맨드 완료 기준 | `analyze-dau.md`에서 "PASS" 검색 | 최소 3개 PASS 기준 존재 |
| MAU 커맨드 파라미터 | `analyze-mau.md`에서 "year_month" 검색 | 파라미터 정의 존재 |
| MAU 비용 명시 | `analyze-mau.md`에서 "USD" 검색 | 비용 추정 포함 |
| dry-run 언급 | 두 커맨드 파일에서 "dry_run" 검색 | 각 파일에 dry-run 절차 포함 |

### 개념 이해 자기 점검

다음 질문에 답할 수 있어야 합니다. 답이 떠오르지 않으면 해당 섹션을 다시 읽으세요.

1. **AGENTS.md와 README.md의 차이**는 무엇인가? *(관찰 1-A 참조)*
2. 에이전트에게 "최선을 다해 분석해줘"라고 하는 것보다 슬래시 커맨드를 사용하는 **구체적인 이점** 3가지는? *(관찰 1-C 참조)*
3. DAU 커맨드에서 `dry_run`을 기본값 `true`로 설정한 **이유**는 무엇인가? *(수정 2-C 참조)*
4. 에이전트 행동 정책에서 dbt 테스트가 실패했을 때 **자동 수정을 금지하는 이유**는? *(관찰 1-B 참조)*
5. 슬래시 커맨드의 "완료 기준"이 없을 때 어떤 문제가 발생하는가? *(관찰 1-E 원칙 5 참조)*

### 다음 모듈 진입 기준

**모든 창작 단계 구현 체크리스트 항목을 통과**해야 모듈 3으로 진행할 수 있습니다.

---

## 모듈 요약

이 모듈에서 배운 핵심 내용을 정리합니다.

**관찰 단계에서 이해한 것**:
- AGENTS.md의 5개 섹션 구조 (프로젝트 개요, 도메인 정의, 아키텍처 규약, 행동 정책, 파일 위치 지도)
- 슬래시 커맨드의 표준 섹션 구조와 `$ARGUMENTS` 플레이스홀더
- 재사용 가능한 분석 커맨드의 5가지 설계 원칙

**수정 단계에서 실습한 것**:
- AGENTS.md에 Stickiness 도메인 정의 추가
- BigQuery 비용 에스컬레이션 3단계 기준 구체화
- 슬래시 커맨드에 `dry_run` 기본값과 FAIL 처리 로직 추가

**창작 단계에서 직접 만든 것**:
- `.claude/commands/analyze-mau.md` — MAU + Stickiness 분석 커맨드
- `AGENTS.md` — 5개 섹션이 모두 포함된 완성본

**다음 모듈 예고**: 모듈 3에서는 `settings.json`의 `permissions` 섹션을 깊이 다루며, 에이전트가 접근할 수 있는 도구와 명령의 경계를 설계합니다. AGENTS.md의 "행동 정책"이 텍스트로 표현되는 것과 달리, permissions는 기계적으로 강제됩니다.

---

*이 문서는 하니스 엔지니어링 코스 — 모듈 2입니다. 독립적으로 생성 가능하며, 다른 모듈 파일에 의존하지 않습니다.*
