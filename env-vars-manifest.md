# Environment Variables Manifest

<!-- Shared reference for all modules. Instructional content in Korean; variable names and
     technical identifiers in English. -->

각 모듈에서 사용하는 환경 변수의 전체 목록입니다.
모듈별로 필요한 변수와 선택적 변수를 구분하여 정리했습니다.

---

## 빠른 참조 — 모듈별 필수 변수

| 변수 이름 | M0 | M1 | M2 | M3 | M4 | 관리 위치 |
|-----------|:--:|:--:|:--:|:--:|:--:|-----------|
| `GCP_PROJECT_ID` | ✅ | ✅ | ✅ | ✅ | ✅ | `.env` |
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ | ✅ | ✅ | ✅ | ✅ | `.env` |
| `BQ_DATASET_RAW` | ✅ | ✅ | ✅ | ✅ | ✅ | `.env` (기본값: `raw`) |
| `BQ_DATASET_ANALYTICS` | ✅ | ✅ | ✅ | ✅ | ✅ | `.env` (기본값: `analytics`) |
| `DATASET_LOCATION` | ○ | ○ | ○ | ○ | ○ | `.env` (기본값: `US`) |
| `BQ_COST_LIMIT_BYTES` | — | ✅ | ✅ | ✅ | ✅ | `settings.json` env 섹션 |
| `GITHUB_REPOSITORY` | — | — | — | ✅ | ✅ | `.env` |
| `CLAUDE_TOKEN` | — | — | — | ✅ | ✅ | GitHub Secret (로컬 불필요) |
| `BQ_COST_WARN_GB` | — | — | — | — | ✅ | `settings.json` env 섹션 |
| `BQ_COST_BLOCK_GB` | — | — | — | — | ✅ | `settings.json` env 섹션 |
| `SYNTHETIC_NUM_USERS` | ○ | ○ | ○ | ○ | ○ | `.env` (기본값: `10000`) |
| `SYNTHETIC_START_DATE` | ○ | ○ | ○ | ○ | ○ | `.env` (기본값: `2026-01-01`) |
| `SYNTHETIC_END_DATE` | ○ | ○ | ○ | ○ | ○ | `.env` (기본값: `2026-03-31`) |

**범례:** ✅ = 필수, ○ = 선택, — = 해당 모듈에서 미사용

---

## 변수 상세 정의

### GCP / BigQuery 인증

#### `GCP_PROJECT_ID`
- **설명:** Google Cloud 프로젝트 ID (전 세계에서 고유한 값)
- **형식:** 소문자 영문자, 숫자, 하이픈 (예: `fittrack-analysis-yourname-2026`)
- **필수 모듈:** 0, 1, 2, 3, 4
- **관리 위치:** `.env` 파일
- **사용처:** `scripts/load_to_bigquery.py`, `scripts/generate_synthetic_data.py`,
  `dbt_project.yml` (`env_var('GCP_PROJECT_ID')`), `profiles.yml`, `.claude/hooks/*.sh`

#### `GOOGLE_APPLICATION_CREDENTIALS`
- **설명:** GCP 서비스 계정 JSON 키 파일의 절대 경로
- **형식:** 절대 경로 문자열 (예: `/tmp/fittrack-sa-key.json`)
- **필수 모듈:** 0, 1, 2, 3, 4
- **관리 위치:** `.env` 파일
- **⚠️ 보안 주의:** 키 파일 자체는 절대 Git에 커밋하지 마세요. 경로만 `.env`에 기록합니다.
  `.env`는 `.gitignore`에 포함되어 있습니다.
- **사용처:** Google Cloud SDK (`gcloud`, `bq`), `google-cloud-bigquery` Python 라이브러리,
  dbt-bigquery 어댑터

---

### BigQuery 데이터셋

#### `BQ_DATASET_RAW`
- **설명:** 원시 이벤트 데이터가 적재되는 BigQuery 데이터셋 이름
- **기본값:** `raw`
- **필수 모듈:** 0, 1, 2, 3, 4
- **관리 위치:** `.env` 파일
- **사용처:** `scripts/load_to_bigquery.py` (테이블 적재 대상),
  `models/staging/sources.yml` (`env_var('BQ_DATASET_RAW')`)

#### `BQ_DATASET_ANALYTICS`
- **설명:** dbt 변환 결과(스테이징 및 마트 모델)가 생성되는 BigQuery 데이터셋 이름
- **기본값:** `analytics`
- **필수 모듈:** 0, 1, 2, 3, 4
- **관리 위치:** `.env` 파일
- **사용처:** `dbt_project.yml` (출력 스키마), `profiles.yml`

#### `DATASET_LOCATION`
- **설명:** BigQuery 데이터셋 물리적 위치 (리전)
- **기본값:** `US`
- **권장 대안:** 아시아 태평양 사용자는 `asia-northeast3` (서울) 권장
- **필수 모듈:** 해당 없음 (선택, 모든 모듈)
- **관리 위치:** `.env` 파일 (주석 처리된 상태 — 필요 시 주석 해제)
- **사용처:** `scripts/bq_setup.sh` (데이터셋 생성 시)

---

### BigQuery 비용 제어

#### `BQ_COST_LIMIT_BYTES`
- **설명:** BigQuery 쿼리 실행 전 드라이 런으로 확인하는 최대 허용 바이트 수.
  이 값을 초과하면 `bq-cost-guard.sh` 훅이 실행을 차단합니다.
- **기본값:** `536870912` (500 MB)
- **필수 모듈:** 1, 2, 3, 4
- **관리 위치:** `.claude/settings.json`의 `env` 섹션
  (`.env` 파일이 아닌 settings.json에서 설정 — 훅 실행 환경에서 자동 주입됨)
- **사용처:** `.claude/hooks/bq-cost-guard.sh`

#### `BQ_COST_WARN_GB`
- **설명:** BigQuery 쿼리 실행 전 경고를 출력할 데이터 처리량 임계값 (GB 단위).
  이 값 초과 시 경고 메시지를 출력하지만 쿼리는 허용합니다.
- **기본값:** `10` (10 GB — 정상 DAU 집계 쿼리 ~2 GB의 5배)
- **필수 모듈:** 4
- **관리 위치:** `.claude/settings.json`의 `env` 섹션
- **사용처:** `.claude/hooks/pre_bq_cost_check.sh` (모듈 4 신규)

#### `BQ_COST_BLOCK_GB`
- **설명:** BigQuery 쿼리 실행을 완전히 차단할 데이터 처리량 임계값 (GB 단위).
  이 값 초과 시 `exit 1`로 쿼리 실행을 차단합니다.
- **기본값:** `40` (40 GB — FitTrack 전체 이벤트 테이블 ~30 GB보다 약간 높게 설정)
- **필수 모듈:** 4
- **관리 위치:** `.claude/settings.json`의 `env` 섹션
- **사용처:** `.claude/hooks/pre_bq_cost_check.sh` (모듈 4 신규)

---

### GitHub / 오케스트레이션

#### `GITHUB_REPOSITORY`
- **설명:** GitHub 리포지토리 경로 (소유자/리포지토리 형식)
- **형식:** `owner/repo-name` (예: `your-username/fittrack-analysis`)
- **필수 모듈:** 3, 4
- **관리 위치:** `.env` 파일
- **사용처:** `.github/workflows/auto-analyze.yml` (워크플로 트리거 경로 참조),
  `gh` CLI 명령

#### `CLAUDE_TOKEN`
- **설명:** GitHub Actions에서 `claude -p` 를 실행하기 위한 Claude 인증 토큰
- **필수 모듈:** 3, 4 (GitHub Actions 환경 전용)
- **관리 위치:** **GitHub Repository Secret** (`CLAUDE_TOKEN`으로 등록)
  — 로컬 `.env`에 입력하지 마세요. 로컬에서는 `claude login`으로 인증합니다.
- **사용처:** `.github/workflows/auto-analyze.yml`의 `ANTHROPIC_API_KEY` 환경 변수

---

### 합성 데이터 생성 (선택)

#### `SYNTHETIC_NUM_USERS`
- **설명:** 합성 데이터 생성 시 사용자 수
- **기본값:** `10000`
- **필수 모듈:** 해당 없음 (선택, 모듈 0~4)
- **관리 위치:** `.env` 파일 (주석 처리된 상태 — 필요 시 주석 해제)
- **사용처:** `scripts/generate_synthetic_data.py`
- **⚠️ 주의:** 수업 환경에서는 기본값(10000) 유지 권장. 값을 늘리면 BigQuery 비용이 증가합니다.

#### `SYNTHETIC_START_DATE`
- **설명:** 합성 이벤트 데이터의 시작 날짜
- **기본값:** `2026-01-01`
- **형식:** ISO 8601 (`YYYY-MM-DD`)
- **필수 모듈:** 해당 없음 (선택, 모듈 0~4)
- **관리 위치:** `.env` 파일 (주석 처리된 상태 — 필요 시 주석 해제)
- **사용처:** `scripts/generate_synthetic_data.py`

#### `SYNTHETIC_END_DATE`
- **설명:** 합성 이벤트 데이터의 종료 날짜
- **기본값:** `2026-03-31`
- **형식:** ISO 8601 (`YYYY-MM-DD`)
- **필수 모듈:** 해당 없음 (선택, 모듈 0~4)
- **관리 위치:** `.env` 파일 (주석 처리된 상태 — 필요 시 주석 해제)
- **사용처:** `scripts/generate_synthetic_data.py`

---

## 모듈별 최소 설정

각 모듈을 독립적으로 시작할 때 반드시 설정해야 하는 변수 목록입니다.

### 모듈 0 (프로젝트 설정)

```bash
# 필수
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# 기본값 사용 가능 (변경 시 설정)
BQ_DATASET_RAW=raw
BQ_DATASET_ANALYTICS=analytics
```

### 모듈 1 (훅과 settings.json)

```bash
# 필수
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# 기본값 사용 가능 (변경 시 설정)
BQ_DATASET_RAW=raw
BQ_DATASET_ANALYTICS=analytics

# settings.json에서 관리 (기본값 변경 시 settings.json 수정)
# BQ_COST_LIMIT_BYTES=536870912  → .claude/settings.json env 섹션
```

### 모듈 2 (슬래시 커맨드)

모듈 1과 동일.

### 모듈 3 (오케스트레이션)

```bash
# 필수
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GITHUB_REPOSITORY=your-username/your-repo-name

# 기본값 사용 가능 (변경 시 설정)
BQ_DATASET_RAW=raw
BQ_DATASET_ANALYTICS=analytics

# settings.json에서 관리
# BQ_COST_LIMIT_BYTES=536870912  → .claude/settings.json env 섹션

# GitHub Secret으로 등록 (로컬 .env에 입력 불필요)
# CLAUDE_TOKEN=...
```

### 모듈 4 (오류 처리와 비용 최적화)

```bash
# 필수
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GITHUB_REPOSITORY=your-username/your-repo-name

# 기본값 사용 가능 (변경 시 설정)
BQ_DATASET_RAW=raw
BQ_DATASET_ANALYTICS=analytics

# settings.json에서 관리 (기본값 변경 시 settings.json 수정)
# BQ_COST_LIMIT_BYTES=536870912  → .claude/settings.json env 섹션
# BQ_COST_WARN_GB=10             → .claude/settings.json env 섹션
# BQ_COST_BLOCK_GB=40            → .claude/settings.json env 섹션

# GitHub Secret으로 등록 (로컬 .env에 입력 불필요)
# CLAUDE_TOKEN=...
```

---

## 관리 위치 설명

### `.env` 파일
각 모듈 루트에 있는 `.env.example`을 `.env`로 복사하여 실제 값을 입력합니다.
`.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.

```bash
cp .env.example .env
# 편집기로 .env를 열고 실제 값 입력
```

### `.claude/settings.json` env 섹션
훅 스크립트에서 사용하는 변수는 `.claude/settings.json`의 `env` 섹션에서 관리합니다.
Claude Code가 훅을 실행할 때 이 값들이 자동으로 환경 변수로 주입됩니다.

```json
{
  "env": {
    "BQ_COST_LIMIT_BYTES": "536870912",
    "BQ_COST_WARN_GB": "10",
    "BQ_COST_BLOCK_GB": "40"
  }
}
```

### GitHub Repository Secret
GitHub Actions 워크플로에서 사용하는 민감한 값은 GitHub Repository Secret으로 등록합니다.
Settings → Secrets and variables → Actions → New repository secret

```
CLAUDE_TOKEN  →  claude 인증 토큰 값
```
