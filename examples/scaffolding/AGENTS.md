# AGENTS.md — 데이터 분석 하니스 에이전트 컨텍스트

> **이 파일은 Claude Code 에이전트가 이 레포지토리에서 작업할 때 자동으로 로드되는
> 규칙·규약·정책 문서입니다.**
> 새 에이전트 세션을 시작할 때마다 이 파일이 컨텍스트로 포함되므로,
> 일관된 동작 기준이 유지됩니다.

---

## 프로젝트 개요

**[프로젝트명]** — B2C 모바일 앱 사용자 행동 분석 프로젝트

| 구성 요소 | 기술 스택 |
|-----------|-----------|
| 데이터 웨어하우스 | BigQuery (On-Demand 가격) |
| 데이터 변환 | dbt (source → staging → intermediate → marts) |
| 분석 노트북 | marimo `.py` 포맷 |
| 자동화 | GitHub Actions + Claude Agent SDK |
| 패키지 관리 | uv (`pyproject.toml`) |

### 핵심 메트릭 정의

| 메트릭 | 정의 | dbt 모델 |
|--------|------|----------|
| DAU | 해당 일자에 1회 이상 이벤트를 발생시킨 고유 사용자 수 | `fct_daily_active_users` |
| MAU | 해당 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수 | `fct_monthly_active_users` |
| Stickiness | DAU / MAU × 100 (%) | 노트북 내 계산 |
| 리텐션율 | 코호트 가입 후 N일 시점 재방문 비율 | `fct_retention_cohort` |

---

## 레포지토리 구조

```
├── AGENTS.md                        # 이 파일 — 에이전트 컨텍스트
├── pyproject.toml                   # uv 의존성 관리
├── setup.sh                         # 로컬 환경 초기화 스크립트
│
├── models/                          # dbt 프로젝트
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml.example
│   ├── staging/
│   │   ├── sources.yml              # BigQuery 소스 정의
│   │   ├── schema.yml               # staging 모델 테스트/문서
│   │   ├── stg_events.sql           # 이벤트 스테이징
│   │   ├── stg_users.sql            # 사용자 스테이징
│   │   └── stg_sessions.sql         # 세션 스테이징
│   ├── intermediate/
│   │   ├── schema.yml
│   │   ├── int_user_daily_activity.sql
│   │   └── int_user_metrics.sql
│   └── marts/
│       ├── schema.yml
│       ├── fct_daily_active_users.sql
│       ├── fct_monthly_active_users.sql
│       └── fct_retention_cohort.sql
│
├── notebooks/                       # marimo 분석 노트북
│   └── analysis_<이슈번호>.py       # 이슈별 분석 노트북
│
├── reports/                         # 내보낸 HTML 리포트 (Git 미추적)
│
├── scripts/
│   └── generate_synthetic_data.py   # 합성 데이터 생성
│
├── .claude/
│   ├── settings.json                # 권한·훅 설정
│   └── commands/                    # 커스텀 슬래시 명령
│       ├── analyze.md               # /analyze — 분석 요청 처리
│       ├── validate-models.md       # /validate-models — dbt 검증
│       ├── generate-report.md       # /generate-report — 리포트 생성
│       ├── check-cost.md            # /check-cost — BQ 비용 확인
│       ├── explore-data.md          # /explore-data — 데이터 탐색
│       └── create-model.md          # /create-model — dbt 모델 생성
│
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── config.yml               # 템플릿 선택 화면 설정
    │   ├── analysis-request.yml     # 분석 요청 (→ auto-analyze 파이프라인)
    │   ├── bug-report.yml           # 버그/데이터 품질 이슈
    │   ├── feature-request.yml      # 기능 요청/개선 제안
    │   └── data-question.yml        # 데이터/메트릭 질의
    ├── scripts/
    │   └── label-setup.sh           # 라벨 일괄 등록 스크립트
    └── workflows/
        ├── auto-analyze.yml         # 7단계 자동 분석 파이프라인
        ├── dbt-ci.yml               # PR 검증 — dbt 빌드/테스트
        └── validate-harness.yml     # 하니스 구성 검증
```

---

## dbt 규약

### 네이밍 규칙

| 계층 | 패턴 | 예시 |
|------|------|------|
| Staging | `stg_<소스테이블명>.sql` | `stg_events.sql` |
| Intermediate | `int_<변환내용>.sql` | `int_user_daily_activity.sql` |
| Mart (팩트) | `fct_<비즈니스_프로세스>.sql` | `fct_daily_active_users.sql` |
| Mart (디멘전) | `dim_<엔티티>.sql` | `dim_users.sql` |

### 모델 작성 규칙

1. 모든 모델은 `{{ config(...) }}` 블록으로 시작
2. staging 모델: `materialized='view'`
3. mart 모델: `materialized='table'`, `partition_by`로 날짜 파티션 설정
4. 소스 참조: 반드시 `{{ source() }}` 또는 `{{ ref() }}` 매크로 사용
5. 하드코딩된 테이블명 직접 참조 **금지**
6. CTE 이름은 역할을 명확히 (예: `filtered_events`, `daily_aggregated`)

### 테스트 규칙

모든 모델에 대해 `schema.yml`에 테스트를 정의합니다:

- **Primary key**: `unique` + `not_null`
- **카테고리 컬럼**: `accepted_values`
- **외래키**: `relationships`

새 모델 추가 시 반드시 `schema.yml`에 컬럼 정의 및 테스트 추가.

### dbt 명령 실행 규칙

```bash
# 개발 환경에서만 실행 (target: dev)
dbt run --target dev

# 변경된 모델만 빌드 (증분 빌드 권장)
dbt run --target dev --select state:modified+

# 전체 리프레시 금지 — 증분 빌드만 허용
# 금지: dbt run --full-refresh

# 테스트는 항상 실행
dbt test
```

---

## BigQuery 정책

### 비용 제어 (On-Demand 가격 기준)

| 규칙 | 설명 |
|------|------|
| Dry-run 선행 | 쿼리 실행 전 반드시 `--dry_run`으로 스캔 바이트 확인 |
| 단일 쿼리 한도 | 스캔 **1 GB** 초과 시 실행 중단 → 쿼리 최적화 필요 |
| SELECT * 금지 | 필요한 컬럼만 명시 |
| 파티션 필터 필수 | 날짜 파티션 테이블 조회 시 날짜 필터 반드시 포함 |
| LIMIT 제한 | 탐색 쿼리에는 `LIMIT 1000` 이하로 제한 |

### 데이터 보호

다음 명령은 **절대 실행 금지**:

```sql
-- 금지: 데이터 파괴
DELETE FROM ...
DROP TABLE ...
TRUNCATE TABLE ...
```

```bash
# 금지: dbt 전체 재빌드
dbt run --full-refresh

# 금지: BigQuery 리소스 삭제
bq rm ...
```

### 데이터셋 구조

```
<project_id>.fittrack_raw       # 원본 데이터 (읽기 전용)
<project_id>.fittrack_dev       # 개발 환경 (읽기/쓰기)
<project_id>.fittrack_prod      # 프로덕션 (dbt CI에서만 쓰기)
```

---

## marimo 노트북 규약

### 파일 구조

- **경로**: `notebooks/analysis_<이슈번호>.py`
- **형식**: marimo 앱 포맷 (`import marimo as mo`로 시작)
- **셀 구성**:
  1. 첫 번째 셀: 분석 제목, 기간, 핵심 발견 요약 (`mo.md`)
  2. 데이터 로드 셀: BigQuery 연결 및 쿼리
  3. 분석 셀: 계산 및 변환
  4. 시각화 셀: 차트/테이블 (plotly 또는 altair)
  5. 마지막 셀: 결론 및 제안 사항 (`mo.md`)

### 코드 스타일

```python
# 변수명/함수명: 영어 (snake_case)
# 코드 주석: 한국어
# 차트 제목/축 레이블/범례: 한국어

import marimo as mo
import pandas as pd
import plotly.express as px
from google.cloud import bigquery

# BigQuery 클라이언트 초기화
client = bigquery.Client(project=PROJECT_ID)

# DAU 데이터 로드 쿼리
query = """
    SELECT
        activity_date,    -- 활동 날짜
        platform,         -- 플랫폼 (iOS/Android)
        dau               -- 일별 활성 사용자 수
    FROM `{project}.fittrack_dev.fct_daily_active_users`
    WHERE activity_date BETWEEN @start_date AND @end_date
    ORDER BY activity_date
"""
```

### 시각화 규칙

- 차트 제목, 축 레이블, 범례: **한국어**
- 숫자 포맷: 천 단위 쉼표, 비율은 소수점 2자리 (%)
- 색상: plotly 기본 팔레트 또는 `#1D76DB` (파란 계열) 일관 사용

---

## 워크플로 규약

### 자동 분석 파이프라인 (7단계)

GitHub Issue에 `auto-analyze` 라벨을 부착하면 자동으로 시작됩니다:

| 단계 | 라벨 | 수행 내용 |
|------|------|-----------|
| 초기화 | `auto-analyze` | Stage 1 라벨로 전환 |
| Stage 1 | `stage:1-problem` | 문제 정의 — 핵심 질문, 분석 범위 정리 |
| Stage 2 | `stage:2-deliverables` | 산출물 명세 — dbt 모델, 노트북 구조 계획 |
| Stage 3 | `stage:3-spec` | 분석 스펙 — SQL 계획, 검증 기준 작성 |
| Stage 4 | `stage:4-extract` | 데이터 추출 — dbt 실행, 데이터 품질 검증 |
| Stage 5 | `stage:5-analyze` | 분석 수행 — marimo 노트북 작성 및 실행 |
| Stage 6 | `stage:6-report` | 리포트 생성 — HTML 내보내기 |
| Stage 7 | `stage:7-pr` | PR 생성 — dbt 모델 + 노트북 소스 포함 |

### PR 규칙

- **PR에 포함**: dbt 모델/쿼리 (`.sql`, `.yml`) + marimo 노트북 소스 (`.py`)
- **PR에 미포함**: HTML/PDF 리포트 (GitHub Actions 아티팩트로 별도 업로드)
- **PR 제목 형식**: `분석: <이슈 제목>`
- **PR 본문**: 이슈 번호 참조 (`Closes #N`), 산출물 목록, 주요 발견 요약

### 에러 처리

1. 실패 시 `status:error` 라벨 자동 부착 + 에러 내용 코멘트
2. 재시도 방법:
   - `status:error` 라벨 제거
   - 실패한 단계의 라벨을 수동으로 재부착
3. 워크플로 로그 링크는 에러 코멘트에 포함됨

---

## 에이전트 역할 정의

이 레포지토리에서 두 가지 역할의 Claude Code 에이전트가 협력하여 분석 작업을 수행합니다.

### 역할 1: GitHub Actions 오케스트레이션 에이전트

**용도**: 7단계 자동 분석 파이프라인을 비대화형(`--print` 모드)으로 실행

| 속성 | 내용 |
|------|------|
| 실행 환경 | GitHub Actions Ubuntu runner |
| 트리거 | Issue `labeled` 이벤트 (라벨 연쇄) |
| 실행 명령 | `npx @anthropic-ai/claude-code --print "..."` |
| 인증 | `ANTHROPIC_API_KEY` (GitHub Secret) |
| GCP 인증 | `GCP_SA_KEY` (GitHub Secret → 임시 파일) |
| 컨텍스트 소스 | 이슈 본문 + 이전 단계 이슈 코멘트 |

**단계별 에이전트 분류**:

| 계층 | 단계 | 허용 도구 | 외부 시스템 |
|------|------|-----------|-------------|
| **설계 계층** | Stage 1~3 (문제 정의, 산출물 명세, 분석 스펙) | Read, Write | 없음 (텍스트 처리만) |
| **실행 계층** | Stage 4 (데이터 추출) | Read, Write, Bash | BigQuery, dbt |
| **분석 계층** | Stage 5 (분석 수행) | Read, Write, Bash | BigQuery |
| **산출 계층** | Stage 6~7 (리포트, PR 생성) | Read, Write, Bash | GitHub API, Git |

**각 단계 에이전트의 책임**:

- **Stage 1 — 문제 정의 에이전트**: 이슈 본문에서 분석 목적, 핵심 질문, 분석 범위, 성공 기준을 구조화 → 이슈 코멘트 출력
- **Stage 2 — 산출물 명세 에이전트**: Stage 1 결과를 읽고 필요한 dbt 모델, 노트북 구조, 리포트 구성 계획 → 이슈 코멘트 출력
- **Stage 3 — 분석 스펙 에이전트**: SQL/dbt 실행 계획, BigQuery 비용 예상, marimo 노트북 상세 설계, 검증 기준 작성 → 이슈 코멘트 출력
- **Stage 4 — 데이터 추출 에이전트**: dbt 실행 (dry-run → 비용 확인 → `dbt run` → `dbt test`) → Git 커밋 (신규 dbt 모델)
- **Stage 5 — 분석 수행 에이전트**: marimo 노트북 작성 (`notebooks/analysis_<N>.py`), BigQuery 쿼리 실행 → Git 커밋 (노트북 소스)
- **Stage 6 — 리포트 생성 에이전트**: marimo → HTML 변환 → GitHub Actions 아티팩트 업로드
- **Stage 7 — PR 생성 에이전트**: 분석 브랜치 생성, dbt 모델 + 노트북 소스 커밋, GitHub PR 생성

---

### 역할 2: 로컬 대화형 에이전트

**용도**: 탐색적 분석, 하니스 개발, 개별 작업 지원

| 속성 | 내용 |
|------|------|
| 실행 환경 | 로컬 개발 환경 |
| 트리거 | `/slash` 명령, 직접 대화 |
| 실행 명령 | `claude` (대화형 모드) |
| 인증 | Claude Code Pro/Max 구독 |
| GCP 인증 | `GOOGLE_APPLICATION_CREDENTIALS` (로컬 파일) |
| 컨텍스트 소스 | AGENTS.md + `.claude/settings.json` + 현재 디렉토리 |

**주요 슬래시 명령 및 책임**:

| 명령 | 파일 | 책임 |
|------|------|------|
| `/analyze` | `.claude/commands/analyze.md` | 분석 요청을 받아 7단계 파이프라인 실행 안내 |
| `/explore-data` | `.claude/commands/explore-data.md` | BigQuery 테이블 탐색, 샘플 쿼리 실행 |
| `/validate-models` | `.claude/commands/validate-models.md` | dbt 모델 검증 (`dbt build + test`) |
| `/create-model` | `.claude/commands/create-model.md` | 새로운 dbt 모델 생성 및 schema.yml 업데이트 |
| `/generate-report` | `.claude/commands/generate-report.md` | marimo 노트북 HTML 내보내기 |
| `/check-cost` | `.claude/commands/check-cost.md` | BigQuery 비용 dry-run 확인 |

---

## 에이전트 작업 가이드라인

### 허용된 작업

- BigQuery 읽기 쿼리 (dry-run 확인 후 1 GB 이내)
- dbt 모델 생성/수정, `dbt run --target dev`, `dbt test`
- marimo 노트북 생성/수정 (`notebooks/` 디렉토리)
- Git 브랜치 생성, 커밋, PR 생성
- GitHub Issues 코멘트 작성, 라벨 전환

### 사람 확인이 필요한 작업

- 새로운 데이터 소스 추가 (`sources.yml` 수정)
- 프로덕션 데이터셋에 대한 쿼리 또는 쓰기
- `.github/workflows/` 워크플로 파일 수정
- `pyproject.toml` 의존성 변경
- `.claude/settings.json` 권한 정책 변경

### 절대 금지 작업

- `DELETE`, `DROP`, `TRUNCATE` SQL 실행
- `dbt run --full-refresh`
- `reports/` 외부 경로에 HTML/PDF 저장
- Secrets 또는 자격증명 파일 (`*.json`, `*.key`, `.env`) 커밋
- `main`/`master` 브랜치에 직접 push
- `bq rm` 명령 실행

---

## 환경 변수

| 변수명 | 설명 | 소스 |
|--------|------|------|
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP 서비스 계정 키 파일 경로 | 로컬: `~/.config/gcp/sa-key.json` |
| `BQ_PROJECT_ID` | BigQuery 프로젝트 ID | `.env` 파일 또는 GitHub Secret |
| `ANTHROPIC_API_KEY` | Claude API 키 | GitHub Secret (CI 전용) |

---

## 로컬 개발 환경 설정

```bash
# 1. 의존성 설치
uv sync

# 2. dbt 프로파일 설정
cp models/profiles.yml.example ~/.dbt/profiles.yml
# profiles.yml에서 project, dataset, key_file 경로 수정

# 3. dbt 연결 테스트
uv run dbt debug

# 4. dbt 패키지 설치
uv run dbt deps

# 5. 합성 데이터 생성 (최초 1회)
uv run python scripts/generate_synthetic_data.py

# 6. dbt 빌드 및 테스트
uv run dbt build --target dev

# 7. marimo 노트북 실행 (개발 모드)
uv run marimo edit notebooks/analysis_1.py
```

---

## GitHub Actions 시크릿 설정

GitHub 레포지토리 Settings → Secrets and variables → Actions에 다음을 등록합니다:

| 시크릿명 | 값 | 설명 |
|----------|----|------|
| `GCP_SA_KEY` | GCP 서비스 계정 JSON 전체 내용 | BigQuery 인증 |
| `BQ_PROJECT_ID` | `my-gcp-project-id` | BigQuery 프로젝트 ID |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Claude API 인증 |

---

## 라벨 설정

레포지토리에 다음 라벨을 등록합니다 (`.github/scripts/label-setup.sh` 실행):

```bash
bash .github/scripts/label-setup.sh
```

| 라벨 | 색상 | 용도 |
|------|------|------|
| `auto-analyze` | `#0075CA` | 자동 분석 파이프라인 트리거 |
| `stage:1-problem` | `#E4E669` | 파이프라인 Stage 1 |
| `stage:2-deliverables` | `#E4E669` | 파이프라인 Stage 2 |
| `stage:3-spec` | `#E4E669` | 파이프라인 Stage 3 |
| `stage:4-extract` | `#FBCA04` | 파이프라인 Stage 4 |
| `stage:5-analyze` | `#FBCA04` | 파이프라인 Stage 5 |
| `stage:6-report` | `#0E8A16` | 파이프라인 Stage 6 |
| `stage:7-pr` | `#0E8A16` | 파이프라인 Stage 7 |
| `done` | `#0E8A16` | 완료 |
| `status:error` | `#D93F0B` | 파이프라인 에러 |
| `분석 요청` | `#0075CA` | 데이터 분석 요청 이슈 |
| `버그` | `#D93F0B` | 버그 신고 이슈 |
| `기능 요청` | `#A2EEEF` | 기능 요청 이슈 |
| `질의` | `#CCF` | 데이터 질의 이슈 |
