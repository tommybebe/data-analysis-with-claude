# 단계 분리 에이전트 아키텍처

> DAU/MAU 분석 파이프라인을 위한 7단계 에이전트 설계 — 역할, 입출력 계약, 에이전트 간 통신 패턴

---

## 1. 아키텍처 개요

### 설계 원칙

7단계 자동 분석 워크플로에서 **각 단계는 독립된 에이전트로 실행**됩니다. GitHub Actions의 `labeled` 이벤트가 트리거되면, 해당 단계에 배정된 에이전트가 Claude Agent SDK(`claude -p`)를 통해 비대화형으로 실행됩니다.

| 원칙 | 설명 |
|------|------|
| **단계 격리** | 각 에이전트는 독립된 GitHub Actions 워크플로 실행(runner)에서 동작하며, 이전 에이전트의 메모리를 공유하지 않음 |
| **명시적 계약** | 입력(이전 단계 산출물)과 출력(현재 단계 산출물)이 JSON/Markdown 스키마로 정의됨 |
| **이슈 코멘트 기반 통신** | 에이전트 간 산출물 전달은 GitHub Issue 코멘트를 매개로 수행 |
| **프롬프트 파일 분리** | 각 에이전트의 지시사항은 `.claude/prompts/stage-N-*.md` 파일에 독립 정의 |
| **도구 최소 권한** | 각 에이전트에 허용되는 도구(Read, Write, Bash 등)를 `--allowedTools`로 제한 |

### 전체 아키텍처 다이어그램

```
                        ┌──────────────────────────────────────────┐
                        │         GitHub Issue (분석 요청)           │
                        │  "FitTrack Q1 DAU/MAU 트렌드 분석"         │
                        └────────────────┬─────────────────────────┘
                                         │ auto-analyze 라벨 부착
                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Orchestrator                          │
│  on: issues.labeled → if: auto-analyze || startsWith('stage:')         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼─────────────────────────┐
        │                        │                         │
        ▼                        ▼                         ▼
  ┌───────────┐          ┌───────────┐              ┌───────────┐
  │ 설계 계층  │          │ 실행 계층  │              │ 산출 계층  │
  │ Stage 1~4 │          │ Stage 5   │              │ Stage 6~7 │
  │ (파랑 🔵)  │          │ (보라 🟣)  │              │ (보라 🟣)  │
  └───────────┘          └───────────┘              └───────────┘
        │                        │                         │
        │ 분석 계획 수립          │ dbt 모델 실행            │ 분석 + 리포트
        ▼                        ▼                         ▼
  Issue Comment           Git Commit              PR (dbt + marimo)
  (JSON/Markdown)        (dbt models)            + HTML/PDF 아티팩트
```

### 에이전트 계층 분류

| 계층 | 단계 | 라벨 색상 | 특성 | 주요 도구 |
|------|------|-----------|------|-----------|
| **설계 계층** | 1~4 | 🔵 파랑 | 텍스트 처리 중심, 외부 시스템 접근 없음 | Read, Write |
| **실행 계층** | 5 | 🟣 보라 | BigQuery/dbt 실행, 외부 시스템 접근 필요 | Read, Write, Bash |
| **산출 계층** | 6~7 | 🟣 보라 | 노트북 작성 + 내보내기 + PR 생성 | Read, Write, Bash |

---

## 2. 에이전트 간 통신 패턴

### 2.1 이슈 코멘트 기반 전달 (Issue Comment Relay)

각 에이전트는 **같은 러너를 공유하지 않습니다**. 단계 간 데이터 전달은 GitHub Issue 코멘트를 매개로 합니다.

```
Agent N (Stage N 실행)
  │
  ├─ 1. 이슈 코멘트에서 이전 단계 산출물 읽기
  │     └─ <!-- stage:(N-1)-complete --> 앵커로 파싱
  │
  ├─ 2. 현재 단계 작업 수행
  │
  └─ 3. 이슈 코멘트에 현재 단계 산출물 기록
        └─ <!-- stage:N-complete --> 앵커 포함
```

### 2.2 코멘트 구조 규약

모든 에이전트의 산출물 코멘트는 다음 형식을 따릅니다:

```markdown
## Stage N 완료: [단계 이름]

### 산출물
[구조화된 JSON 또는 Markdown]

### 완료 증거
- [검증 결과]

### 다음 단계 입력
- [다음 에이전트가 사용할 핵심 정보]

<!-- stage:N-complete -->
```

### 2.3 Git 커밋 기반 전달 (Git Commit Relay)

Stage 5~7에서는 **파일 산출물이 Git 커밋으로 레포에 저장**됩니다. 다음 단계 실행 시 `actions/checkout@v4`로 최신 커밋을 체크아웃하면, 이전 단계가 생성한 파일에 접근할 수 있습니다.

```
Stage 5 Agent
  └─ dbt 모델 파일 생성 → git commit + push
                                │
Stage 6 Agent                   │
  └─ actions/checkout@v4 ───────┘ (최신 커밋 포함)
     └─ dbt 모델 파일 접근 가능 → marimo 노트북 작성 → git commit + push
                                                            │
Stage 7 Agent                                               │
  └─ actions/checkout@v4 ──────────────────────────────────┘
     └─ dbt 모델 + marimo 노트북 접근 가능 → HTML/PDF 내보내기 → PR 생성
```

### 2.4 이중 전달 메커니즘 요약

| 전달 방식 | 사용 단계 | 전달 내용 | 특징 |
|-----------|-----------|-----------|------|
| **이슈 코멘트** | 전 단계 (1→2→3→4→5→6→7) | 분석 계획, 스펙, 검증 결과 등 텍스트 기반 산출물 | 러너 간 공유 가능, 파싱 앵커로 검색 |
| **Git 커밋** | 실행/산출 계층 (5→6→7) | dbt 모델 파일, marimo 노트북 소스 | 다음 checkout에서 파일 접근, PR에 포함 |

---

## 3. 단계별 에이전트 상세 명세

### Stage 1: Parse Agent (이슈 파싱 에이전트)

**역할**: GitHub Issue 본문을 구조화된 분석 요청 객체로 변환

```
┌─────────────────────────────────────────────┐
│              Parse Agent                     │
│  라벨: stage:1-parse                         │
│  프롬프트: .claude/prompts/stage-1-parse.md  │
│  max-turns: 5                                │
│  allowedTools: Read, Write                   │
├─────────────────────────────────────────────┤
│  입력:                                       │
│    • github.event.issue.body (이슈 본문)     │
│    • github.event.issue.title (이슈 제목)    │
│                                              │
│  처리:                                       │
│    1. 이슈 본문에서 템플릿 필드 추출          │
│    2. 분석 기간, 세그먼트, 유형 등 파싱       │
│    3. 유효성 검증 (필수 필드 누락 확인)       │
│                                              │
│  출력:                                       │
│    • request.json (이슈 코멘트에 기록)        │
└─────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 | 필수 |
|------|------|------|------|
| `issue_title` | `github.event.issue.title` | string | ✓ |
| `issue_body` | `github.event.issue.body` | Markdown (템플릿 기반) | ✓ |

**출력 계약** (`request.json`):

```json
{
  "title": "2026년 1분기 DAU/MAU 트렌드 분석",
  "problem_statement": "FitTrack 앱의 2026년 1분기 DAU와 MAU 추이를 파악하고...",
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "primary_segment": "platform",
  "secondary_segments": [],
  "analysis_type": "trend",
  "expected_deliverables": [
    "일별 DAU 추이 차트 (라인 차트, 플랫폼별 색상 구분)",
    "월별 MAU 추이 차트 (바 차트)",
    "DAU/MAU 비율 트렌드 (플랫폼별 라인 차트)",
    "주요 발견 요약 (3~5문장)"
  ],
  "filters": {
    "exclude_test_accounts": true,
    "test_account_pattern": "test_*"
  },
  "additional_context": "주말 효과가 예상되므로 요일별 패턴도 함께 확인"
}
```

**완료 증거**: JSON 스키마 필수 필드 존재 확인, `date_range.start < date_range.end` 검증

---

### Stage 2: Define Agent (문제 정의 에이전트)

**역할**: 비즈니스 질문을 구체적이고 측정 가능한 분석 질문으로 변환

```
┌─────────────────────────────────────────────┐
│              Define Agent                    │
│  라벨: stage:2-define                        │
│  프롬프트: .claude/prompts/stage-2-define.md │
│  max-turns: 8                                │
│  allowedTools: Read, Write                   │
├─────────────────────────────────────────────┤
│  입력:                                       │
│    • Stage 1 산출물 (request.json)           │
│    • AGENTS.md (데이터 카탈로그 참조)         │
│    • dbt sources.yml (사용 가능한 테이블)     │
│                                              │
│  처리:                                       │
│    1. 비즈니스 질문 → 분석 질문 분해          │
│    2. 각 질문에 대한 메트릭 정의              │
│    3. 데이터 소스 매핑 (어느 테이블 사용?)    │
│    4. 가설 명시 (검증 가능한 형태)            │
│                                              │
│  출력:                                       │
│    • problem_statement.md (이슈 코멘트 기록)  │
└─────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| `request.json` | Stage 1 이슈 코멘트 (`<!-- stage:1-complete -->`) | JSON |
| 데이터 카탈로그 | `AGENTS.md` 내 테이블 목록 | Markdown |
| dbt 소스 정의 | `models/staging/sources.yml` | YAML |

**출력 계약** (`problem_statement.md`):

```markdown
# 문제 정의서: 2026년 Q1 DAU/MAU 트렌드 분석

## 분석 질문
1. 2026년 Q1 동안 일별 DAU는 어떤 추세를 보이는가?
2. 월별 MAU는 어떻게 변화했는가?
3. DAU/MAU 비율(stickiness)은 플랫폼(iOS/Android)별로 차이가 있는가?
4. 주말 vs 평일 DAU 패턴에 유의미한 차이가 존재하는가?

## 메트릭 정의
| 메트릭 | 정의 | 산식 |
|--------|------|------|
| DAU | 특정 날짜에 1회 이상 이벤트를 발생시킨 고유 사용자 수 | COUNT(DISTINCT user_id) WHERE date = target_date |
| MAU | 특정 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수 | COUNT(DISTINCT user_id) WHERE month = target_month |
| Stickiness | 해당 월의 DAU 평균 / MAU | AVG(daily_dau) / mau |

## 데이터 소스 매핑
| 테이블 | 사용 목적 | 주요 컬럼 |
|--------|-----------|-----------|
| raw_events | 사용자 활동 이벤트 | user_id, event_timestamp, event_name, platform |
| raw_users | 사용자 프로필 (가입일, 플랫폼) | user_id, created_at, platform |

## 가설
- H1: Android 사용자의 stickiness가 iOS 대비 10%p 이상 낮다
- H2: 주말 DAU는 평일 대비 15% 이상 감소한다

## 필터/제외 조건
- 테스트 계정 제외: user_id가 'test_'로 시작하는 계정
```

**완료 증거**: 분석 질문 최소 3개 정의, 각 메트릭에 SQL 산식 포함, 데이터 소스 매핑 테이블 존재

---

### Stage 3: Deliverables Agent (산출물 명세 에이전트)

**역할**: 최종 분석 리포트에 포함될 산출물(차트, 테이블, 텍스트) 목록을 구체적으로 정의

```
┌──────────────────────────────────────────────────┐
│              Deliverables Agent                   │
│  라벨: stage:3-deliverables                       │
│  프롬프트: .claude/prompts/stage-3-deliverables.md│
│  max-turns: 8                                     │
│  allowedTools: Read, Write                        │
├──────────────────────────────────────────────────┤
│  입력:                                            │
│    • Stage 1 산출물 (request.json)                │
│    • Stage 2 산출물 (problem_statement.md)        │
│                                                   │
│  처리:                                            │
│    1. 분석 질문별 필요 산출물 도출                  │
│    2. 각 산출물의 유형(차트/테이블/텍스트) 분류     │
│    3. 차트 사양 정의 (축, 색상, 범례 등)           │
│    4. 데이터 요구사항 역산 (어떤 쿼리 결과 필요?)  │
│                                                   │
│  출력:                                            │
│    • deliverables.json (이슈 코멘트에 기록)        │
└──────────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| `request.json` | Stage 1 이슈 코멘트 | JSON |
| `problem_statement.md` | Stage 2 이슈 코멘트 | Markdown |

**출력 계약** (`deliverables.json`):

```json
{
  "deliverables": [
    {
      "id": "D1",
      "type": "line_chart",
      "title": "일별 DAU 추이 (플랫폼별)",
      "description": "2026-01-01 ~ 2026-03-31 기간의 일별 DAU를 iOS/Android로 구분하여 표시",
      "x_axis": "date",
      "y_axis": "dau",
      "color_by": "platform",
      "data_source": "mart_dau_daily",
      "answers_question": "Q1: 일별 DAU 추세"
    },
    {
      "id": "D2",
      "type": "bar_chart",
      "title": "월별 MAU 추이",
      "description": "2026년 1~3월 MAU를 월별 바 차트로 표시",
      "x_axis": "month",
      "y_axis": "mau",
      "data_source": "mart_mau_monthly",
      "answers_question": "Q2: 월별 MAU 변화"
    },
    {
      "id": "D3",
      "type": "line_chart",
      "title": "DAU/MAU 비율 (Stickiness) 트렌드",
      "description": "월별 stickiness를 플랫폼별로 비교",
      "x_axis": "month",
      "y_axis": "stickiness_ratio",
      "color_by": "platform",
      "data_source": "mart_stickiness_monthly",
      "answers_question": "Q3: 플랫폼별 stickiness 차이"
    },
    {
      "id": "D4",
      "type": "box_plot",
      "title": "요일별 DAU 분포",
      "description": "요일(월~일)별 DAU 분포를 박스플롯으로 비교",
      "x_axis": "day_of_week",
      "y_axis": "dau",
      "data_source": "mart_dau_daily",
      "answers_question": "Q4: 주말 vs 평일 패턴"
    },
    {
      "id": "D5",
      "type": "summary_text",
      "title": "주요 발견 요약",
      "description": "분석 결과에서 도출된 핵심 인사이트 3~5문장",
      "answers_question": "전체 요약"
    }
  ],
  "data_requirements": [
    {
      "model_name": "mart_dau_daily",
      "grain": "date × platform",
      "columns": ["date", "platform", "dau"]
    },
    {
      "model_name": "mart_mau_monthly",
      "grain": "month × platform",
      "columns": ["month", "platform", "mau"]
    },
    {
      "model_name": "mart_stickiness_monthly",
      "grain": "month × platform",
      "columns": ["month", "platform", "avg_dau", "mau", "stickiness_ratio"]
    }
  ]
}
```

**완료 증거**: 모든 분석 질문에 최소 1개 산출물 매핑, 각 차트 산출물에 축/색상 정의 포함

---

### Stage 4: Spec Agent (스펙 작성 에이전트)

**역할**: dbt 모델 쿼리 계획과 marimo 노트북 구조를 상세 설계

```
┌─────────────────────────────────────────────┐
│              Spec Agent                      │
│  라벨: stage:4-spec                          │
│  프롬프트: .claude/prompts/stage-4-spec.md   │
│  max-turns: 10                               │
│  allowedTools: Read, Write                   │
├─────────────────────────────────────────────┤
│  입력:                                       │
│    • Stage 2 산출물 (problem_statement.md)   │
│    • Stage 3 산출물 (deliverables.json)      │
│    • 기존 dbt 모델 (models/ 디렉토리)        │
│    • dbt sources.yml                         │
│    • AGENTS.md (dbt 컨벤션)                  │
│                                              │
│  처리:                                       │
│    1. 기존 mart 모델 재사용 여부 판단         │
│    2. 신규 dbt 모델 SQL 의사코드 작성         │
│    3. marimo 노트북 셀 구조 설계              │
│    4. 쿼리 비용 추정 (BigQuery dry-run)       │
│                                              │
│  출력:                                       │
│    • spec.md (이슈 코멘트에 기록)             │
└─────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| `problem_statement.md` | Stage 2 이슈 코멘트 | Markdown |
| `deliverables.json` | Stage 3 이슈 코멘트 | JSON |
| 기존 dbt 모델 | `models/` 디렉토리 (checkout) | SQL 파일 |
| dbt 컨벤션 | `AGENTS.md` 내 dbt 규칙 섹션 | Markdown |

**출력 계약** (`spec.md`):

```markdown
# 분석 스펙: DAU/MAU 트렌드 분석

## dbt 모델 계획

### 재사용 기존 모델
- `stg_events` (staging): raw_events → 이벤트 정규화
- `stg_users` (staging): raw_users → 사용자 프로필

### 신규/수정 모델

#### `mart_dau_daily.sql`
```sql
-- grain: date × platform
-- 일별, 플랫폼별 DAU 계산
SELECT
  DATE(event_timestamp) AS date,
  u.platform,
  COUNT(DISTINCT e.user_id) AS dau
FROM {{ ref('stg_events') }} e
JOIN {{ ref('stg_users') }} u ON e.user_id = u.user_id
WHERE u.user_id NOT LIKE 'test_%'
GROUP BY 1, 2
```

#### `mart_mau_monthly.sql`
```sql
-- grain: month × platform
SELECT
  DATE_TRUNC(DATE(event_timestamp), MONTH) AS month,
  u.platform,
  COUNT(DISTINCT e.user_id) AS mau
FROM {{ ref('stg_events') }} e
JOIN {{ ref('stg_users') }} u ON e.user_id = u.user_id
WHERE u.user_id NOT LIKE 'test_%'
GROUP BY 1, 2
```

#### `mart_stickiness_monthly.sql`
```sql
-- grain: month × platform
-- stickiness = AVG(daily DAU) / MAU
WITH daily AS (
  SELECT * FROM {{ ref('mart_dau_daily') }}
),
monthly AS (
  SELECT * FROM {{ ref('mart_mau_monthly') }}
)
SELECT
  monthly.month,
  monthly.platform,
  AVG(daily.dau) AS avg_dau,
  monthly.mau,
  SAFE_DIVIDE(AVG(daily.dau), monthly.mau) AS stickiness_ratio
FROM monthly
JOIN daily ON DATE_TRUNC(daily.date, MONTH) = monthly.month
  AND daily.platform = monthly.platform
GROUP BY 1, 2, 4
```

## marimo 노트북 구조

| 셀 번호 | 셀 이름 | 내용 | 의존 데이터 |
|---------|---------|------|------------|
| 1 | imports | 라이브러리 import (marimo, altair, pandas) | — |
| 2 | config | BigQuery 연결 설정, 프로젝트 ID | — |
| 3 | load_dau | mart_dau_daily 데이터 로드 | mart_dau_daily |
| 4 | load_mau | mart_mau_monthly 데이터 로드 | mart_mau_monthly |
| 5 | load_stickiness | mart_stickiness_monthly 데이터 로드 | mart_stickiness_monthly |
| 6 | chart_dau_trend | D1: 일별 DAU 라인 차트 | load_dau |
| 7 | chart_mau_trend | D2: 월별 MAU 바 차트 | load_mau |
| 8 | chart_stickiness | D3: Stickiness 라인 차트 | load_stickiness |
| 9 | chart_weekday | D4: 요일별 DAU 박스플롯 | load_dau |
| 10 | summary | D5: 주요 발견 요약 텍스트 | 모든 데이터 |

## 쿼리 비용 추정
- BigQuery dry-run으로 스캔 바이트 사전 확인
- 예상 스캔량: 합성 데이터 기준 ~50MB 이하
```

**완료 증거**: 모든 `deliverables.json`의 `data_source`에 대응하는 dbt 모델 SQL 존재, marimo 셀 구조에 모든 산출물 ID(D1~D5) 포함

---

### Stage 5: Extract Agent (데이터 추출 에이전트)

**역할**: dbt 모델을 실행하여 BigQuery에 mart 테이블을 생성하고 데이터를 검증

```
┌─────────────────────────────────────────────────┐
│              Extract Agent                       │
│  라벨: stage:5-extract                           │
│  프롬프트: .claude/prompts/stage-5-extract.md    │
│  max-turns: 15                                   │
│  allowedTools: Read, Write, Bash                 │
├─────────────────────────────────────────────────┤
│  입력:                                           │
│    • Stage 4 산출물 (spec.md)                    │
│    • 기존 dbt 프로젝트 (models/, dbt_project.yml)│
│    • AGENTS.md (dbt 컨벤션)                      │
│                                                  │
│  처리:                                           │
│    1. spec.md의 SQL 의사코드 → 실제 dbt 모델 작성│
│    2. dbt 모델 파일 생성 (models/mart/*.sql)     │
│    3. schema.yml에 모델 메타데이터 추가           │
│    4. `dbt run --select mart_dau_daily+` 실행    │
│    5. `dbt test` 실행 (데이터 검증)              │
│    6. 결과를 Git 커밋 + 푸시                     │
│                                                  │
│  출력:                                           │
│    • dbt 모델 파일 (Git 커밋)                    │
│    • dbt 실행/테스트 결과 (이슈 코멘트)          │
└─────────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| `spec.md` | Stage 4 이슈 코멘트 (`<!-- stage:4-complete -->`) | Markdown |
| dbt 프로젝트 | 레포 checkout (`models/`, `dbt_project.yml`) | 파일 시스템 |
| GCP 인증 | `GOOGLE_APPLICATION_CREDENTIALS` 환경변수 | JSON 키 파일 |

**출력 계약**:

| 산출물 | 형식 | 전달 방식 |
|--------|------|-----------|
| `models/mart/mart_dau_daily.sql` | SQL | Git 커밋 |
| `models/mart/mart_mau_monthly.sql` | SQL | Git 커밋 |
| `models/mart/mart_stickiness_monthly.sql` | SQL | Git 커밋 |
| `models/mart/schema.yml` (수정) | YAML | Git 커밋 |
| dbt run 결과 | 텍스트 (성공/실패, 행 수) | 이슈 코멘트 |
| dbt test 결과 | 텍스트 (통과/실패 테스트 목록) | 이슈 코멘트 |

**완료 증거**: `dbt run` 종료 코드 0, `dbt test` 전 테스트 통과, mart 테이블에 행 존재 확인

**Bash 명령 허용 범위**:

```bash
# 허용되는 명령
dbt run --select "mart_dau_daily mart_mau_monthly mart_stickiness_monthly"
dbt test --select "mart_dau_daily mart_mau_monthly mart_stickiness_monthly"
dbt run --select "model_name" --dry-run  # 비용 사전 확인
git add models/mart/
git commit -m "feat: add DAU/MAU mart models for issue #N"
git push

# 금지되는 명령
dbt run --full-refresh  # 전체 테이블 재생성 (비용 위험)
bq query "DROP TABLE ..."  # 직접 DDL 금지
```

---

### Stage 6: Analyze Agent (분석 수행 에이전트)

**역할**: marimo 노트북을 작성하여 데이터 분석 및 시각화 수행

```
┌──────────────────────────────────────────────────┐
│              Analyze Agent                        │
│  라벨: stage:6-analyze                            │
│  프롬프트: .claude/prompts/stage-6-analyze.md     │
│  max-turns: 20                                    │
│  allowedTools: Read, Write, Bash                  │
├──────────────────────────────────────────────────┤
│  입력:                                            │
│    • Stage 3 산출물 (deliverables.json)           │
│    • Stage 4 산출물 (spec.md)                     │
│    • Stage 5 산출물 (dbt 실행 결과)               │
│    • dbt mart 모델 파일 (Git checkout)            │
│                                                   │
│  처리:                                            │
│    1. marimo 노트북 파일 생성 (.py)               │
│    2. BigQuery에서 mart 데이터 로드 셀 작성       │
│    3. deliverables.json의 각 산출물별 시각화 셀    │
│    4. 인사이트 요약 텍스트 셀 작성                 │
│    5. marimo run으로 노트북 실행 검증              │
│    6. Git 커밋 + 푸시                             │
│                                                   │
│  출력:                                            │
│    • marimo 노트북 (.py) (Git 커밋)               │
│    • 노트북 실행 결과 요약 (이슈 코멘트)          │
└──────────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| `deliverables.json` | Stage 3 이슈 코멘트 | JSON |
| `spec.md` | Stage 4 이슈 코멘트 | Markdown |
| dbt 실행 결과 | Stage 5 이슈 코멘트 | 텍스트 |
| mart 모델 파일 | Git checkout | SQL 파일 |

**출력 계약**:

| 산출물 | 형식 | 전달 방식 |
|--------|------|-----------|
| `analyses/dau_mau_analysis.py` | Python (marimo 노트북 소스) | Git 커밋 |
| 노트북 셀 실행 성공 여부 | 텍스트 | 이슈 코멘트 |
| 차트 미리보기 (텍스트 설명) | Markdown | 이슈 코멘트 |

**marimo 노트북 구조 규약**:

```python
# analyses/dau_mau_analysis.py
import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")

@app.cell
def imports():
    import marimo as mo
    import altair as alt
    import pandas as pd
    from google.cloud import bigquery
    return alt, bigquery, mo, pd

@app.cell
def load_dau(bigquery, pd):
    # mart_dau_daily에서 데이터 로드
    client = bigquery.Client()
    query = """
    SELECT date, platform, dau
    FROM `project.dataset.mart_dau_daily`
    ORDER BY date
    """
    df_dau = client.query(query).to_dataframe()
    return df_dau,

# ... (각 산출물별 셀 계속)
```

**완료 증거**: marimo 노트북 파일 존재 확인, `marimo run analyses/dau_mau_analysis.py` 종료 코드 0, `deliverables.json`의 모든 산출물 ID에 대응하는 셀 존재

---

### Stage 7: Report Agent (리포트 생성 에이전트)

**역할**: marimo 노트북을 HTML/PDF로 내보내고, 분석 산출물을 포함한 PR을 생성

```
┌──────────────────────────────────────────────────┐
│              Report Agent                         │
│  라벨: stage:7-report                             │
│  프롬프트: .claude/prompts/stage-7-report.md      │
│  max-turns: 15                                    │
│  allowedTools: Read, Write, Bash                  │
├──────────────────────────────────────────────────┤
│  입력:                                            │
│    • Stage 6 산출물 (marimo 노트북 .py)           │
│    • Stage 2 산출물 (problem_statement.md)        │
│    • 이슈 메타데이터 (번호, 제목)                  │
│                                                   │
│  처리:                                            │
│    1. marimo export로 HTML/PDF 정적 문서 생성     │
│    2. PR 본문 작성 (분석 요약 + 산출물 목록)      │
│    3. gh pr create 실행                           │
│    4. HTML/PDF를 Actions 아티팩트로 업로드         │
│    5. 이슈에 PR 링크 코멘트 기록                  │
│                                                   │
│  출력:                                            │
│    • PR (dbt 모델 + marimo 소스만 포함)           │
│    • HTML/PDF 아티팩트 (Actions 아티팩트)          │
│    • 이슈 완료 코멘트                             │
└──────────────────────────────────────────────────┘
```

**입력 계약**:

| 필드 | 소스 | 형식 |
|------|------|------|
| marimo 노트북 | Git checkout (`analyses/dau_mau_analysis.py`) | Python |
| `problem_statement.md` | Stage 2 이슈 코멘트 | Markdown |
| 이슈 번호 | `github.event.issue.number` | 정수 |

**출력 계약**:

| 산출물 | 형식 | 전달 방식 |
|--------|------|-----------|
| `reports/dau_mau_analysis.html` | HTML | Actions 아티팩트 (PR에 미포함) |
| `reports/dau_mau_analysis.pdf` | PDF | Actions 아티팩트 (PR에 미포함) |
| PR | GitHub Pull Request | `gh pr create` |
| 완료 코멘트 | Markdown | 이슈 코멘트 |

**PR 포함 파일 규칙**:

```
PR에 포함 (Git 커밋):
  ✓ models/mart/mart_dau_daily.sql
  ✓ models/mart/mart_mau_monthly.sql
  ✓ models/mart/mart_stickiness_monthly.sql
  ✓ models/mart/schema.yml
  ✓ analyses/dau_mau_analysis.py   (marimo 소스)

PR에 미포함 (Actions 아티팩트만):
  ✗ reports/dau_mau_analysis.html   → actions/upload-artifact
  ✗ reports/dau_mau_analysis.pdf    → actions/upload-artifact
```

**Bash 명령 허용 범위**:

```bash
# 허용되는 명령
marimo export html analyses/dau_mau_analysis.py -o reports/dau_mau_analysis.html
marimo export pdf analyses/dau_mau_analysis.py -o reports/dau_mau_analysis.pdf
gh pr create --title "분석: DAU/MAU 트렌드 (#N)" --body "..."
git add models/ analyses/
git commit -m "feat: DAU/MAU analysis for issue #N"
git push

# 금지되는 명령
git add reports/  # HTML/PDF는 Git에 커밋하지 않음
```

**완료 증거**: PR 생성 확인 (`gh pr view`로 URL 반환), HTML/PDF 파일 존재 확인 (`ls reports/`), PR에 `reports/` 디렉토리 파일 미포함 확인

---

## 4. 에이전트 실행 환경 설정

### 공통 환경 (모든 에이전트)

모든 에이전트 실행 전에 GitHub Actions 워크플로에서 공통으로 설정되는 환경:

```yaml
steps:
  # 공통 설정 (모든 단계에서 실행)
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: '3.12'
  - run: curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync
  - run: echo '${{ secrets.GCP_SA_KEY }}' > /tmp/gcp-key.json
  - run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}
```

### 단계별 에이전트 실행 명령

| 단계 | 실행 명령 | `--max-turns` | `--allowedTools` |
|------|-----------|---------------|------------------|
| 1 | `claude -p "$(cat .claude/prompts/stage-1-parse.md) ..."` | 5 | `Read,Write` |
| 2 | `claude -p "$(cat .claude/prompts/stage-2-define.md) ..."` | 8 | `Read,Write` |
| 3 | `claude -p "$(cat .claude/prompts/stage-3-deliverables.md) ..."` | 8 | `Read,Write` |
| 4 | `claude -p "$(cat .claude/prompts/stage-4-spec.md) ..."` | 10 | `Read,Write` |
| 5 | `claude -p "$(cat .claude/prompts/stage-5-extract.md) ..."` | 15 | `Read,Write,Bash` |
| 6 | `claude -p "$(cat .claude/prompts/stage-6-analyze.md) ..."` | 20 | `Read,Write,Bash` |
| 7 | `claude -p "$(cat .claude/prompts/stage-7-report.md) ..."` | 15 | `Read,Write,Bash` |

### 컨텍스트 주입 패턴

각 에이전트 실행 시, 프롬프트에 이슈 컨텍스트와 이전 단계 산출물을 주입합니다:

```bash
# 프롬프트 구성: 프롬프트 파일 + 이슈 컨텍스트 + 이전 산출물
PROMPT="$(cat .claude/prompts/stage-${STAGE_NUM}-${STAGE_NAME}.md)

## 이슈 컨텍스트
이슈 번호: #${ISSUE_NUMBER}
이슈 제목: ${ISSUE_TITLE}
이슈 본문:
${ISSUE_BODY}

## 이전 단계 산출물
${PREVIOUS_STAGE_COMMENTS}"

claude -p "$PROMPT" --max-turns ${MAX_TURNS} --allowedTools "${ALLOWED_TOOLS}"
```

---

## 5. 에이전트 간 의존성 그래프

```
Stage 1 (Parse)
  │
  ├──→ request.json
  │       │
  ▼       ▼
Stage 2 (Define)
  │
  ├──→ problem_statement.md
  │       │        │
  ▼       │        │
Stage 3 (Deliverables)
  │       │        │
  ├──→ deliverables.json
  │       │        │
  │       ▼        ▼
  │    Stage 4 (Spec)
  │       │
  │       ├──→ spec.md
  │       │
  │       ▼
  │    Stage 5 (Extract)    ← Bash 도구 필요 (dbt run)
  │       │
  │       ├──→ dbt 모델 파일 (Git 커밋)
  │       ├──→ dbt 실행 결과 (이슈 코멘트)
  │       │
  │       ▼
  └──→ Stage 6 (Analyze)    ← Bash 도구 필요 (marimo run)
          │
          ├──→ marimo 노트북 .py (Git 커밋)
          │
          ▼
       Stage 7 (Report)     ← Bash 도구 필요 (marimo export, gh pr create)
          │
          ├──→ HTML/PDF (Actions 아티팩트)
          └──→ PR 생성
```

### 입력 의존 매트릭스

어느 에이전트가 어느 이전 단계의 산출물을 참조하는지:

| 현재 단계 ↓ / 참조 단계 → | S1 | S2 | S3 | S4 | S5 | S6 |
|---------------------------|:--:|:--:|:--:|:--:|:--:|:--:|
| **Stage 2** | ✓ | — | — | — | — | — |
| **Stage 3** | ✓ | ✓ | — | — | — | — |
| **Stage 4** | — | ✓ | ✓ | — | — | — |
| **Stage 5** | — | — | — | ✓ | — | — |
| **Stage 6** | — | — | ✓ | ✓ | ✓ | — |
| **Stage 7** | — | ✓ | — | — | — | ✓ |

---

## 6. 오류 처리 및 재시도 전략

### 에이전트 실패 시 동작

```
에이전트 실행 실패 (종료 코드 ≠ 0)
  │
  ├─ 1. 현재 단계 라벨 유지 (예: stage:5-extract)
  ├─ 2. stage:error 라벨 추가 부착
  ├─ 3. 이슈에 오류 상세 코멘트 작성
  │     (실패 단계, 워크플로 실행 URL, 오류 메시지)
  └─ 4. 워크플로 종료 (다음 단계로 전환하지 않음)
```

### 단계별 재시도 안전성

| 단계 | 멱등성 | 재시도 안전성 | 주의사항 |
|------|--------|-------------|---------|
| 1 (Parse) | ✓ 멱등 | 안전 | 이슈 본문이 변하지 않는 한 동일 결과 |
| 2 (Define) | ✓ 멱등 | 안전 | LLM 출력 변동성 있으나, 구조적으로 동등 |
| 3 (Deliverables) | ✓ 멱등 | 안전 | 위와 동일 |
| 4 (Spec) | ✓ 멱등 | 안전 | 위와 동일 |
| 5 (Extract) | △ 조건부 | 주의 필요 | `dbt run`은 멱등 (CREATE OR REPLACE), 단 이전 Git 커밋이 중복될 수 있음 |
| 6 (Analyze) | △ 조건부 | 주의 필요 | 노트북 파일 덮어쓰기 가능, 이전 커밋 이력에 중복 |
| 7 (Report) | △ 조건부 | 주의 필요 | PR 중복 생성 방지를 위해 기존 PR 존재 여부 확인 필요 |

### 재시도 절차

```bash
# 1. 오류 원인 확인 (Actions 로그)
gh run view <RUN_ID> --log-failed

# 2. stage:error 라벨 제거
gh issue edit <ISSUE_NUMBER> --remove-label "stage:error"

# 3. 실패 단계 라벨 제거 후 재부착 (재트리거)
gh issue edit <ISSUE_NUMBER> --remove-label "stage:5-extract"
gh issue edit <ISSUE_NUMBER> --add-label "stage:5-extract"
```

---

## 7. 자기 점검 체크리스트

| # | 점검 항목 | 검증 방법 |
|---|----------|----------|
| 1 | 7개 에이전트의 역할을 각각 1문장으로 설명할 수 있다 | 이 문서의 각 에이전트 "역할" 문장과 대조하여 핵심 키워드 일치 확인 |
| 2 | 설계 계층(1~4)과 실행/산출 계층(5~7)의 차이를 설명할 수 있다 | 설계 계층은 Read/Write만 사용, 실행/산출 계층은 Bash 도구 추가 사용이라는 점을 설명 가능 |
| 3 | 에이전트 간 통신이 이슈 코멘트와 Git 커밋 두 경로로 이뤄지는 이유를 설명할 수 있다 | 러너 격리(독립 워크플로 실행)로 파일 시스템 미공유, 코멘트는 텍스트 전달, Git은 파일 전달 |
| 4 | `<!-- stage:N-complete -->` 앵커의 용도를 설명할 수 있다 | 다음 에이전트가 이전 산출물을 프로그래밍 방식으로 파싱하기 위한 검색 앵커 |
| 5 | 입력 의존 매트릭스에서 Stage 6이 S3, S4, S5를 모두 참조하는 이유를 설명할 수 있다 | S3(산출물 명세)에서 차트 사양, S4(스펙)에서 노트북 구조, S5(추출 결과)에서 데이터 가용성 확인 |
| 6 | Stage 5~7의 재시도가 "조건부 안전"인 이유를 설명할 수 있다 | dbt는 멱등이나 Git 커밋 중복 가능, PR 중복 생성 가능성이 있어 확인 로직 필요 |
| 7 | `GITHUB_TOKEN` 대신 `GITHUB_PAT`을 사용하는 이유를 설명할 수 있다 | `GITHUB_TOKEN`으로 부착한 라벨은 연쇄 워크플로를 트리거하지 못함 (무한 루프 방지 정책) |
| 8 | 각 에이전트의 `--max-turns` 값이 다른 이유를 설명할 수 있다 | 작업 복잡도에 비례: 파싱(5턴)은 단순, 분석(20턴)은 시각화 반복 수정 가능성으로 높게 설정 |
