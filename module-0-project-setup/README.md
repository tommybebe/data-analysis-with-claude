# 모듈 0: 프로젝트 설정 — 하니스 엔지니어링 입문과 환경 준비

> **학습 시간**: 2~3시간 (개념 학습 30분 + 환경 설치 60분 + 실습 30~60분)
> **모듈 유형**: 오리엔테이션 (실습 전 준비 단계)
> **사전 모듈**: 없음 — 이 모듈이 코스의 시작점입니다
> **기술 사전 조건**: SQL/dbt/Python 실무 경험, Claude Code Pro/Max 구독, GitHub 계정, GCP 계정

---

## 목차

1. [이 코스에 대하여](#이-코스에-대하여)
2. [이 모듈에서 배우는 것](#이-모듈에서-배우는-것)
3. [실습 프로젝트 소개](#실습-프로젝트-소개-fittrack-dauMAU-분석)
4. [미리 제공되는 파일 vs 직접 만드는 파일](#미리-제공되는-파일-vs-직접-만드는-파일)
5. [시작하기](#시작하기)
   - [사전 요구사항 확인](#사전-요구사항-확인)
   - [단계 1: 이 디렉터리 열기](#단계-1-이-디렉터리-열기)
   - [단계 2: Python 환경 설정](#단계-2-python-환경-설정)
   - [단계 3: GCP 서비스 계정 설정](#단계-3-gcp-서비스-계정-설정)
   - [단계 4: GitHub Secrets 등록](#단계-4-github-secrets-등록)
   - [단계 5: Claude Code 인증](#단계-5-claude-code-인증)
   - [단계 6: 합성 데이터 생성 스크립트 작성 및 BigQuery 적재](#단계-6-합성-데이터-생성-스크립트-작성-및-bigquery-적재)
   - [단계 7: dbt 프로젝트 설정 및 모델 작성](#단계-7-dbt-프로젝트-설정-및-모델-작성)
6. [핵심 개념 소개](#핵심-개념-소개)
7. [모듈 완료 체크리스트](#모듈-완료-체크리스트)
8. [다음 모듈](#다음-모듈)

---

## 이 코스에 대하여

이 코스는 **하니스 엔지니어링(harness engineering)** — Claude Code를 데이터 분석 에이전트로 효과적으로 활용하기 위해 레포지토리를 설계·구성하는 역량 — 을 다룹니다.

**핵심 전제**: 코딩 에이전트의 성능은 모델 능력만으로 결정되지 않습니다. 에이전트가 작업하는 레포지토리의 구조, 정책, 피드백 루프가 결과 품질을 좌우합니다.

```
에이전트 결과 품질 = 모델 능력 × 하니스 품질
```

### 코스 구성 (5개 모듈)

| 모듈 | 디렉터리 | 핵심 질문 |
|------|----------|-----------|
| **0** | **`module-0-project-setup/`** (지금 여기) | **하니스 엔지니어링이란? 환경은 어떻게 준비하는가?** |
| 1 | `module-1-hooks/` | 에이전트가 BigQuery 비용 정책을 스스로 지키게 하려면? |
| 2 | `module-2-slash-commands/` | 반복 분석 작업을 재사용 가능한 명령으로 추상화하려면? |
| 3 | `module-3-orchestration/` | 에이전트가 이 레포를 어떻게 이해하고, 어디까지 접근하는가? |
| 4 | `module-4-error-handling/` | 이슈 하나로 전체 분석 사이클을 자동화하려면? |

각 모듈은 독립적으로 시작할 수 있습니다. 모듈 1~4 디렉터리에는 이전 모듈 완료 상태의 스냅샷이 포함되어 있습니다.

---

## 이 모듈에서 배우는 것

모듈 0은 코스 전체의 **오리엔테이션**입니다. 모듈 1~4가 하니스의 특정 계층을 구현하는 실습 중심이라면, 모듈 0은 데이터 인프라를 구축하고 핵심 개념을 이해하는 준비 단계입니다.

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- **하니스 엔지니어링**이 무엇인지, 왜 경력 데이터 분석가에게 지금 필요한지 설명할 수 있습니다
- 로컬 개발 환경(uv, dbt, marimo, Claude Code CLI)을 정상 설치하고 검증할 수 있습니다
- GCP 서비스 계정을 생성하고 BigQuery 접근 권한을 부여할 수 있습니다
- Python 스크립트로 합성 FitTrack 데이터를 생성하고 BigQuery에 적재할 수 있습니다
- dbt 프로젝트를 설정하고 DAU/MAU 분석 모델을 처음 실행할 수 있습니다
- **하니스 설정(harness configuration)**과 **파이프라인 산출물(pipeline output)**의 차이를 예시와 함께 설명할 수 있습니다
- 이후 모듈(1~4)에서 구현할 하니스의 세 계층 개념을 설명할 수 있습니다

### 이 모듈에서 직접 만드는 것

모듈 0은 **데이터 인프라 구축**이 핵심입니다. Claude Code 에이전트가 사용할 환경을 직접 설계합니다.

| 직접 수행하는 작업 | 결과물 |
|-------------------|--------|
| GCP 프로젝트 생성 및 서비스 계정 설정 | 서비스 계정 JSON 키 |
| GitHub Secrets 등록 | `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, `GITHUB_PAT` |
| dbt 프로젝트 초기화 | `dbt_project.yml`, `packages.yml` |
| 합성 데이터 생성 스크립트 작성 | `scripts/generate_synthetic_data.py` |
| BigQuery 적재 스크립트 작성 | `scripts/load_to_bigquery.py` |
| dbt profiles.yml 작성 | `~/.dbt/profiles.yml` |
| dbt 스테이징 모델 작성 | `models/staging/stg_events.sql`, `stg_users.sql` |
| dbt 마트 모델 작성 | `models/marts/fct_daily_active_users.sql` 외 2개 |

> **모듈 1~4에서 만들 것**: `.claude/settings.json`, `.claude/hooks/`, `.claude/commands/` (슬래시 커맨드), `AGENTS.md`, `.github/workflows/`는 이후 모듈에서 구현합니다.

---

## 실습 프로젝트 소개: FitTrack DAU/MAU 분석

코스 전체에서 동일한 실습 프로젝트를 사용합니다.

**FitTrack** — B2C 피트니스 모바일 앱의 사용자 참여도 분석

| 항목 | 내용 |
|------|------|
| 분석 목표 | DAU(일간 활성 사용자), MAU(월간 활성 사용자), 코호트 리텐션 추적 |
| 데이터 | 합성 이벤트 데이터 (~50만 건/분기), 사용자 프로필 (~1만 명) |
| 데이터 스택 | BigQuery (on-demand) + dbt + marimo |
| 자동화 스택 | GitHub Issues → GitHub Actions → Claude Agent SDK → PR |

**왜 합성 데이터인가?** 프라이버시 보호, 완전한 재현성, 비용 예측 가능성 때문입니다. 실제 사용자 데이터 없이도 동일한 통계적 특성을 재현하도록 설계하며, 누구나 동일한 실습 결과를 기대할 수 있습니다.

**BigQuery 비용 안내**: 이 코스의 실습 범위에서 BigQuery on-demand 비용은 수강생 1인당 **약 $1~5** 수준입니다. 합성 데이터가 소규모로 설계되어 있으며, 모듈 1에서 비용 제어 훅을 직접 구현합니다.

### dbt 모델 구조 (모듈 0에서 구축)

```
BigQuery 데이터셋 구조

raw (원시 데이터)
├── raw_events       ← 합성 이벤트 로그 (~50만 건)
└── raw_users        ← 사용자 프로필 (~1만 명)

analytics (dbt 변환 결과)
├── stg_events       ← 이벤트 클렌징, KST 타임존 통일 (view)
├── stg_users        ← 사용자 프로필 정규화 (view)
├── fct_daily_active_users    ← DAU 집계 (grain: 날짜, table)
├── fct_monthly_active_users  ← MAU 집계 (grain: 연-월, table)
└── fct_retention_cohort      ← D1/D7/D30 코호트 리텐션 (table)
```

---

## 미리 제공되는 파일 vs 직접 만드는 파일

이 모듈은 **최소 스타터**만 제공됩니다 — 나머지는 직접 구축합니다.

### 미리 제공되는 파일 (이 디렉터리에 존재)

```
module-0-project-setup/
├── pyproject.toml              ← Python 의존성 (dbt-bigquery, marimo, 데이터 생성 라이브러리)
├── .env.example                ← 필요한 환경 변수 목록 및 설명
├── CLAUDE.md                   ← Claude Code 에이전트 지침 (영문)
├── references/                 ← 참고 자료 (GCP 설정, 비용 관리, 합성 데이터 가이드)
└── .claude/
    └── commands/
        └── validate.md         ← /validate 커맨드 — 모듈 완료 검증
```

> **왜 이것만 제공하는가?** 하니스 엔지니어링의 핵심은 "환경을 스스로 설계하는 능력"입니다. 스크립트, dbt 모델, 설정 파일을 직접 작성하면서 각 구성 요소가 어떻게 연결되는지 이해하게 됩니다.

### 직접 만드는 파일

```
module-0-project-setup/
├── .env                            ← 환경 변수 (gitignore됨, .env.example 참고)
├── .gitignore                      ← .env, *.json 키 파일, profiles.yml 제외
├── dbt_project.yml                 ← dbt 프로젝트 설정
├── packages.yml                    ← dbt 패키지 목록 (dbt-utils 포함)
├── profiles.yml.example            ← BigQuery 연결 설정 템플릿 (커밋용)
├── scripts/
│   ├── generate_synthetic_data.py  ← 합성 이벤트 데이터 생성기
│   └── load_to_bigquery.py         ← BigQuery 적재 스크립트
└── models/
    ├── staging/
    │   ├── sources.yml             ← BigQuery 소스 정의
    │   ├── schema.yml              ← 스테이징 모델 테스트·문서
    │   ├── stg_events.sql          ← 이벤트 클렌징
    │   └── stg_users.sql           ← 사용자 프로필 정규화
    └── marts/
        ├── schema.yml              ← 마트 모델 테스트·문서
        ├── fct_daily_active_users.sql
        ├── fct_monthly_active_users.sql
        └── fct_retention_cohort.sql

~/.dbt/profiles.yml                 ← dbt BigQuery 연결 설정 (홈 디렉터리, gitignore)
```

---

## 시작하기

아래 단계를 **순서대로** 진행하세요. 각 단계 마지막의 검증 명령어로 정상 완료 여부를 확인하세요.

### 사전 요구사항 확인

설치를 시작하기 전에 다음 계정과 구독이 준비되어 있어야 합니다.

| 항목 | 필요 이유 | 준비 방법 |
|------|-----------|-----------|
| **Claude Code Pro/Max 구독** | Claude Code CLI 및 Agent SDK 사용에 필수 | [claude.ai/code](https://claude.ai/code) 에서 구독 |
| **GitHub 계정** | 레포 포크·클론, Actions, Issues | [github.com](https://github.com) |
| **GCP 계정** | BigQuery 접근 (on-demand 과금) | [cloud.google.com](https://cloud.google.com) — 신규 계정 $300 크레딧 제공 |
| **macOS 또는 Linux** | CLI 명령어 실행 환경 | Windows는 WSL2로 지원 |

**기술 사전 조건**:

| 영역 | 요구 수준 |
|------|-----------|
| SQL | BigQuery SQL 작성 가능 (파티션 쿼리, CTE, 집계 함수) |
| dbt | `dbt run`, `dbt test`, 소스·모델·테스트 YAML 작성 경험 |
| Python | `pandas`, `google-cloud-bigquery` 라이브러리 사용 경험 |
| Git/GitHub | 브랜치, PR, 커밋 기본 작업 |
| CLI | bash/zsh 기본 명령어 사용 |

> **수업 참여자에게**: 최소 3일 전에 GCP 계정·프로젝트를 생성하세요. 당일 생성은 진행 지연의 가장 흔한 원인입니다.

---

### 단계 1: 이 디렉터리 열기

이 모듈은 독립된 프로젝트 루트입니다. 다른 모듈 디렉터리와 교차 참조 없이 단독으로 동작합니다.

```bash
# 이 모듈 디렉터리로 이동
cd module-0-project-setup

# 현재 디렉터리 구조 확인 (최소 스타터만 존재 — 정상)
ls -la
```

**이 디렉터리에서 Claude Code 세션 시작**:

```bash
claude
```

Claude Code는 이 디렉터리의 `CLAUDE.md`를 자동으로 읽어 프로젝트 컨텍스트를 파악합니다. `/validate` 커맨드로 진행 상황을 언제든지 확인할 수 있습니다.

---

### 단계 2: Python 환경 설정

이 프로젝트는 `uv`를 Python 패키지 관리자로 사용합니다.

```bash
# uv 설치 (미설치 시)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 또는 source ~/.zshrc

# uv 버전 확인
uv --version
# 예상 출력: uv 0.x.x

# 프로젝트 의존성 설치 (pyproject.toml 기준)
uv sync

# dbt 버전 확인
uv run dbt --version
# 예상 출력: dbt-core 1.x.x (dbt-bigquery x.x.x 포함)

# marimo 버전 확인
uv run marimo --version
# 예상 출력: marimo 0.x.x

# Claude Code CLI 설치 확인
claude --version
# 예상 출력: claude 1.x.x
# 미설치 시: npm install -g @anthropic-ai/claude-code
```

**성공 기준**: `uv`, `dbt`, `marimo`, `claude` 네 명령 모두 오류 없이 버전 번호 출력

---

### 단계 3: GCP 서비스 계정 설정

BigQuery 접근을 위한 GCP 서비스 계정을 생성하고 인증 키를 등록합니다.

#### 3-1. GCP 프로젝트 및 서비스 계정 생성

```bash
# GCP CLI 인증 (브라우저 인증 창이 열립니다)
gcloud auth login

# 새 프로젝트 생성 (이미 프로젝트가 있으면 스킵)
# GCP_PROJECT_ID는 전 세계에서 고유해야 합니다 (예: fittrack-analysis-yourname-2026)
export GCP_PROJECT_ID="fittrack-analysis-<your-unique-id>"

gcloud projects create $GCP_PROJECT_ID --name="FitTrack Analysis"
gcloud config set project $GCP_PROJECT_ID

# BigQuery API 활성화
gcloud services enable bigquery.googleapis.com

# 서비스 계정 생성
gcloud iam service-accounts create fittrack-agent \
  --display-name="FitTrack Agent Service Account"

# 권한 부여
# bigquery.dataEditor: 테이블 생성·수정 (dbt run에 필요)
# bigquery.jobUser: 쿼리 실행 (모든 BigQuery 작업에 필요)
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:fittrack-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:fittrack-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

#### 3-2. JSON 키 파일 생성

```bash
# JSON 키 생성 (이 파일은 비밀 정보 — 절대 Git에 커밋하지 마세요)
gcloud iam service-accounts keys create /tmp/fittrack-sa-key.json \
  --iam-account=fittrack-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# 키 파일 생성 확인
ls -la /tmp/fittrack-sa-key.json
```

> **보안 주의**: `/tmp/fittrack-sa-key.json`은 GitHub Secrets 등록 후 바로 삭제하세요.

#### 3-3. .env 파일 생성

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일을 편집하여 실제 값 입력
# GCP_PROJECT_ID=fittrack-analysis-<your-unique-id>
# GOOGLE_APPLICATION_CREDENTIALS=/tmp/fittrack-sa-key.json
# (나머지 값은 기본값 사용 가능)
```

> **주의**: `.env` 파일은 Git에 커밋되지 않습니다. 비밀 정보를 안전하게 보관하세요.

---

### 단계 4: GitHub Secrets 등록

GitHub Actions(모듈 4)에서 BigQuery와 Claude에 접근하기 위한 인증 정보를 등록합니다.

```bash
# GitHub CLI 인증 (미인증 시)
gh auth login

# GCP 서비스 계정 JSON 키 등록
gh secret set GCP_SA_KEY < /tmp/fittrack-sa-key.json

# GCP 프로젝트 ID 등록
gh secret set GCP_PROJECT_ID --body "$GCP_PROJECT_ID"

# 키 파일 삭제 (등록 완료 후)
rm /tmp/fittrack-sa-key.json

# 등록 확인 (값은 마스킹되어 표시됩니다)
gh secret list
```

**성공 기준**: `gh secret list` 출력에 `GCP_SA_KEY`, `GCP_PROJECT_ID`가 표시됨

#### GitHub PAT 등록 (GitHub Actions 내 Git 작업용)

```bash
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 스코프: repo (전체), workflow
# 생성 후:
gh secret set GITHUB_PAT --body "<YOUR_PAT_TOKEN>"
```

---

### 단계 5: Claude Code 인증

```bash
# Claude Code 로그인 (브라우저 인증 창이 열립니다)
claude login

# 로그인 상태 확인
claude whoami
# 예상 출력: your.email@example.com (Pro/Max 구독)

# 비대화형 모드 테스트 (GitHub Actions에서 사용하는 방식)
claude -p "1부터 5까지 숫자를 출력해줘." --output-format text

# Claude Agent SDK용 토큰 생성 및 GitHub Secrets 등록
claude setup-token
# 출력된 토큰을 복사하여:
gh secret set CLAUDE_TOKEN --body "<SETUP_TOKEN_OUTPUT>"
```

**성공 기준**:
- `claude whoami` → 이메일 주소 출력
- `claude -p "..."` → 숫자 목록 출력 (오류 없음)
- `gh secret list` → `CLAUDE_TOKEN` 표시

> **토큰 만료 시 갱신**: `claude login` → `claude setup-token` → `gh secret set CLAUDE_TOKEN`

---

### 단계 6: 합성 데이터 생성 스크립트 작성 및 BigQuery 적재

이 단계에서는 Python 스크립트를 직접 작성하여 합성 데이터를 생성하고 BigQuery에 적재합니다.

#### 6-1. 프로젝트 기본 파일 생성

먼저 `.gitignore`를 생성합니다:

```bash
cat > .gitignore << 'EOF'
# Environment and secrets
.env
*.json
!pyproject.json
profiles.yml

# Python
.venv/
__pycache__/
*.pyc
*.egg-info/
dist/
build/

# dbt
target/
dbt_packages/
logs/

# Data files
data/
*.csv
EOF
```

#### 6-2. scripts/ 디렉터리 생성

```bash
mkdir -p scripts
```

#### 6-3. 합성 데이터 생성 스크립트 작성

`scripts/generate_synthetic_data.py`를 작성합니다. 이 스크립트는 다음 데이터를 생성합니다:

- **raw_users**: 약 1만 명의 사용자 프로필
  - 컬럼: `user_id`, `signup_date`, `platform` (ios/android), `subscription_tier` (free/premium)
- **raw_events**: 약 50만 건의 앱 이벤트 로그 (2026년 1분기)
  - 컬럼: `event_id`, `user_id`, `event_type`, `event_timestamp`, `session_id`
  - 이벤트 유형: `app_open`, `workout_start`, `workout_complete`, `profile_view`, `settings_change`

환경 변수 참고:
- `SYNTHETIC_NUM_USERS`: 사용자 수 (기본값: 10000)
- `SYNTHETIC_START_DATE`: 시작 날짜 (기본값: 2026-01-01)
- `SYNTHETIC_END_DATE`: 종료 날짜 (기본값: 2026-03-31)

Claude Code를 활용해 작성하는 것을 권장합니다:

```bash
# Claude Code에게 스크립트 작성 요청
claude
# > scripts/generate_synthetic_data.py를 작성해줘.
# > 약 1만 명의 사용자와 50만 건의 이벤트를 생성하고,
# > data/ 디렉터리에 CSV로 저장하는 스크립트야.
# > .env.example의 환경 변수를 참고해.
```

#### 6-4. BigQuery 적재 스크립트 작성

`scripts/load_to_bigquery.py`를 작성합니다:
- `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수 사용
- `BQ_DATASET_RAW` 데이터셋에 `raw_events`, `raw_users` 테이블 생성
- `google-cloud-bigquery` 라이브러리 사용
- 기존 테이블은 `WRITE_TRUNCATE`로 덮어쓰기

#### 6-5. 스크립트 실행

```bash
# 환경 변수 로드
export $(grep -v '^#' .env | xargs)

# 합성 데이터 생성 (로컬에 CSV 파일 생성)
uv run python scripts/generate_synthetic_data.py

# BigQuery에 적재
uv run python scripts/load_to_bigquery.py
```

생성되는 테이블:

| 테이블 | 레코드 수 (약) | 설명 |
|--------|---------------|------|
| `raw.raw_events` | 500,000건 | 2026년 1분기 앱 이벤트 로그 |
| `raw.raw_users` | 10,000명 | 사용자 프로필 (가입일, 플랫폼, 구독 등급) |

```sql
-- BigQuery 콘솔 또는 bq CLI로 적재 확인 (예상 비용: $0 — 메타데이터 조회)
SELECT table_id, row_count, size_bytes / 1024 / 1024 AS size_mb
FROM `<GCP_PROJECT_ID>.raw.__TABLES__`
ORDER BY table_id;
```

**성공 기준**: `raw_events` ~50만 건, `raw_users` ~1만 명 조회

---

### 단계 7: dbt 프로젝트 설정 및 모델 작성

#### 7-1. dbt 프로젝트 파일 생성

**`dbt_project.yml`** 작성:

```yaml
# dbt_project.yml
name: 'fittrack'
version: '1.0.0'
config-version: 2

profile: 'fittrack'

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
analysis-paths: ["analyses"]
macro-paths: ["macros"]

target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  fittrack:
    staging:
      +materialized: view
      +schema: analytics
    marts:
      +materialized: table
      +schema: analytics
```

**`packages.yml`** 작성:

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
```

#### 7-2. profiles.yml 작성

dbt는 `~/.dbt/profiles.yml`에서 BigQuery 연결 정보를 읽습니다.

```bash
# 홈 디렉터리에 dbt 설정 디렉터리 생성
mkdir -p ~/.dbt

# profiles.yml 작성
cat > ~/.dbt/profiles.yml << 'EOF'
fittrack:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: "{{ env_var('GCP_PROJECT_ID') }}"
      dataset: analytics
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"
      location: US
      timeout_seconds: 300
      threads: 4
EOF
```

**커밋용 템플릿** (`profiles.yml.example`) 작성:

```bash
cat > profiles.yml.example << 'EOF'
# profiles.yml.example — BigQuery 연결 설정 템플릿
# 이 파일을 ~/.dbt/profiles.yml에 복사하고 env_var()로 실제 값을 주입합니다.
# profiles.yml 자체는 절대 커밋하지 마세요 (.gitignore에 포함).
fittrack:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: "{{ env_var('GCP_PROJECT_ID') }}"
      dataset: analytics
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"
      location: US
      timeout_seconds: 300
      threads: 4
EOF
```

#### 7-3. dbt 모델 작성

```bash
mkdir -p models/staging models/marts
```

**`models/staging/sources.yml`** 작성 (BigQuery 소스 정의):

```yaml
version: 2
sources:
  - name: raw
    project: "{{ env_var('GCP_PROJECT_ID') }}"
    dataset: raw
    tables:
      - name: raw_events
        description: "FitTrack 앱 이벤트 로그"
      - name: raw_users
        description: "사용자 프로필"
```

**스테이징 모델** (`models/staging/stg_events.sql`, `stg_users.sql`) 작성:
- `stg_events.sql`: `{{ source('raw', 'raw_events') }}` 참조, `event_timestamp`를 KST(UTC+9)로 변환, 컬럼 선택 및 타입 캐스팅
- `stg_users.sql`: `{{ source('raw', 'raw_users') }}` 참조, 컬럼 정규화

**마트 모델** 작성:
- `fct_daily_active_users.sql`: `{{ ref('stg_events') }}`에서 DAU 집계, `partition_by` DATE 포함
- `fct_monthly_active_users.sql`: MAU 집계, `partition_by` DATE_TRUNC('month') 포함
- `fct_retention_cohort.sql`: `{{ ref('stg_users') }}`와 `{{ ref('stg_events') }}` 조인, D1/D7/D30 리텐션 계산

> **dbt 모델 작성 시 규칙**: 하드코딩된 프로젝트 ID 금지 — 항상 `{{ source() }}`, `{{ ref() }}`, `{{ env_var('GCP_PROJECT_ID') }}` 사용

#### 7-4. schema.yml 작성

각 모델에 대한 컬럼 문서화와 테스트를 `schema.yml`에 작성합니다:
- primary key 컬럼: `unique` + `not_null` 테스트
- 카테고리 컬럼: `accepted_values` 테스트
- 외래 키 컬럼: `relationships` 테스트

#### 7-5. dbt 실행 및 검증

```bash
# 환경 변수 로드
export $(grep -v '^#' .env | xargs)

# BigQuery 연결 확인
uv run dbt debug
# 예상 출력: "All checks passed!"

# dbt 패키지 설치
uv run dbt deps

# 모든 모델 빌드
uv run dbt run
# 예상 출력: Completed successfully — ERROR 0

# 데이터 품질 테스트
uv run dbt test
# 예상 출력: FAIL 0
```

**실패 시 체크리스트**:
1. `dbt debug`에서 BigQuery 연결 오류 확인
2. `~/.dbt/profiles.yml`의 `project`, `keyfile` 경로 확인
3. 서비스 계정에 `bigquery.dataEditor` + `bigquery.jobUser` 권한 확인
4. 환경 변수 `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 설정 확인

---

## 핵심 개념 소개

이 섹션은 코스 전체에서 반복 등장하는 핵심 개념입니다. 모듈 1~4를 진행하며 이 개념들이 구체적인 코드와 연결됩니다.

### 하니스 엔지니어링이란

**하니스 엔지니어링(harness engineering)**은 에이전트 코딩 도구인 Claude Code가 데이터 분석 작업을 안전하고 일관되게 수행하도록 레포지토리를 설계·구성하는 역량입니다.

| 구분 | 정의 | 예시 |
|------|------|------|
| **하니스 설정** | 에이전트의 실행 환경을 구성하는 설정·정책·피드백 루프 | `settings.json`, `AGENTS.md`, 훅 스크립트, GitHub Actions 워크플로 |
| **파이프라인 산출물** | 하니스가 구동하는 에이전트가 만들어내는 결과물 | BigQuery 분석 결과, dbt 모델, marimo 리포트 |

> **이 코스에서 여러분이 직접 만드는 것은 하니스입니다.** 분석 결과물은 하니스를 통해 에이전트가 자동으로 생성합니다.

**왜 이 구분이 중요한가?**

수강생이 흔히 빠지는 함정: *"Claude Code가 dbt 모델을 잘 만들어주면 되지, 하니스가 왜 필요한가?"*

답: 에이전트가 단 한 번 올바른 결과를 내는 것은 쉽습니다. **일관되게, 안전하게, 검증 가능하게** 작업하도록 만드는 것이 하니스 엔지니어링입니다. 하니스 없는 에이전트는 매번 다른 방식으로 일하며, 비용을 초과하거나, 검증을 건너뛰거나, 파이프라인 산출물을 잘못 덮어씁니다.

### 하니스의 세 계층

```
┌────────────────────────────────────────────────────────┐
│         계층 3: 오케스트레이션 (Orchestration)          │
│   GitHub Actions + Claude Agent SDK                   │
│   → 모듈 4에서 구현                                   │
├────────────────────────────────────────────────────────┤
│           계층 2: 스킬과 훅 (Skills & Hooks)           │
│   Claude Code 슬래시 커맨드 + settings.json 훅         │
│   → 모듈 1(훅), 모듈 2(슬래시 커맨드)에서 구현        │
├────────────────────────────────────────────────────────┤
│           계층 1: 스캐폴딩 (Scaffolding)               │
│   AGENTS.md + 데이터 계약 + Issue 템플릿               │
│   → 모듈 3에서 구현                                   │
└────────────────────────────────────────────────────────┘
```

모듈 0에서는 어떤 하니스 계층도 구현하지 않습니다 — 하니스가 구동할 **데이터 인프라(BigQuery + dbt)**만 구축합니다. 하니스는 모듈 1부터 단계적으로 쌓아갑니다.

### 기술 스택 개요

| 구성 요소 | 기술 | 역할 |
|-----------|------|------|
| 데이터 웨어하우스 | BigQuery (on-demand) | 원시 데이터 저장 및 분석 쿼리 |
| 데이터 변환 | dbt | raw → staging → marts 파이프라인 |
| 분석 노트북 | marimo | 시각화·리포트 (모듈 2에서 도입) |
| 하니스 에이전트 | Claude Code | 로컬 개발 에이전트 |
| CI/CD 에이전트 | Claude Agent SDK + GitHub Actions | 자동화 워크플로 (모듈 4) |
| 패키지 관리 | uv | Python 의존성 관리 |

---

## 모듈 완료 체크리스트

Claude Code에서 `/validate`를 실행하면 아래 항목을 자동으로 검증합니다.

| # | 항목 | 검증 방법 | 성공 기준 |
|---|------|-----------|-----------|
| 0 | 환경 변수 설정 | `.env` 파일 기반 환경 변수 확인 | `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 설정됨 |
| 1 | Claude Code CLI | `claude --version` | 버전 번호 출력 |
| 2 | Claude Code 인증 | `claude whoami` | 이메일 주소 출력 |
| 3 | uv | `uv --version` | 버전 번호 출력 |
| 4 | dbt | `uv run dbt --version` | core 버전 + bigquery 어댑터 출력 |
| 5 | marimo | `uv run marimo --version` | 버전 번호 출력 |
| 6 | GitHub Secrets | `gh secret list` | `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, `GITHUB_PAT` 표시 |
| 7 | BigQuery 데이터 적재 | `bq query` 조회 | `raw_events` ~50만 건, `raw_users` ~1만 명 |
| 8 | dbt 모델 빌드·테스트 | `uv run dbt run && uv run dbt test` | `ERROR 0`, `FAIL 0` |

모든 항목이 ✅이면 이 모듈이 완료된 것입니다.

> `/validate` 명령으로 모듈 완료 상태를 확인할 수 있습니다.

---

> **용어 안내**: 이 코스에서 사용하는 하니스 관련 용어(훅, 스캐폴딩, 오케스트레이션 등)는 아직 한국어 공식 표준이 없습니다. 이 문서에서는 에이전트 퍼스트 개발에 고유한 기술 용어로서 영문 원어를 음차하여 사용합니다.
