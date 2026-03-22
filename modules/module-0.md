# 모듈 0: 오리엔테이션 — 하니스 엔지니어링 입문과 환경 준비

> **학습 시간**: 1.5~2시간 (개요 읽기 30분 + 환경 설치 60~90분)
> **모듈 유형**: 오리엔테이션 (실습 전 준비 단계 — 다른 모듈과 구조가 다릅니다)
> **전제 조건**: SQL/dbt/Python 실무 경험

---

## 목차

1. [개요](#개요) — 이 코스가 무엇을 가르치는가, 왜 지금 필요한가
2. [설치](#설치) — 로컬 환경 구성, GCP 연결, GitHub Secrets 등록
3. [개념 소개](#개념-소개) — 하니스 엔지니어링의 핵심 개념과 용어 정의
4. [자기 점검 체크리스트](#자기-점검-체크리스트)

---

## 개요

### 이 코스는 무엇을 가르치는가

이 코스는 **하니스 엔지니어링(harness engineering)** — 에이전트 코딩 도구인 Claude Code가 데이터 분석 작업을 안전하고 일관되게 수행하도록 레포지토리를 설계·구성하는 역량 — 을 다룹니다.

하니스(harness)는 자동차의 안전 장치에서 온 은유입니다. 레이싱 시트 하니스는 드라이버를 제약하는 것처럼 보이지만, 실제로는 더 안전하게 더 빠르게 달릴 수 있도록 합니다. 에이전트 하니스도 마찬가지입니다. 에이전트의 자율성을 제한하는 것이 아니라, **올바른 방향으로 자율적으로 작동하도록** 환경을 정의하는 것입니다.

#### 두 가지 혼동을 피하세요

이 코스를 시작하기 전에 다음 두 가지를 명확히 구분해야 합니다:

| 구분 | 정의 | 예시 |
|------|------|------|
| **하니스 (harness)** | 에이전트가 올바르게 작동하도록 만드는 설정·문서·정책 | `settings.json`, `AGENTS.md`, 훅 스크립트 |
| **파이프라인 산출물 (pipeline output)** | 하니스가 구동하는 에이전트가 만들어내는 결과물 | BigQuery 분석 결과, dbt 모델, marimo 리포트 |

이 코스에서 여러분이 **직접 만드는 것은 하니스**입니다. 분석 결과물은 하니스를 통해 에이전트가 자동으로 생성합니다. 이 구분을 항상 유지하세요.

#### 에이전트 성능의 두 결정 요인

```
에이전트 결과 품질 = 모델 능력 × 하니스 품질
```

동일한 모델(Claude)이라도 하니스 품질에 따라 결과가 크게 달라집니다. 현장에서 에이전트 실패의 원인을 분석하면, 모델 한계보다 **하니스 부재**가 훨씬 더 자주 등장합니다.

**실패 패턴 1 — 비용 통제 부재**

에이전트에게 BigQuery 쿼리 실행을 요청했는데, 파티션 필터 없이 전체 테이블을 스캔하여 예상의 10배 비용이 발생한다. *원인*: 비용 정책 훅 없음.

**실패 패턴 2 — 메트릭 정의 불일치**

에이전트가 DAU를 계산했는데, 팀의 정의(세션 기준)가 아닌 이벤트 기준으로 집계한다. *원인*: 데이터 계약이 코드로 선언되지 않음.

**실패 패턴 3 — 조용한 실패**

자동화 파이프라인이 실행되었지만 dbt 모델 빌드 실패가 감지되지 않아 잘못된 리포트가 PR로 올라온다. *원인*: 검증 훅과 승인 게이트 없음.

이 세 패턴은 각각 하니스의 세 계층 — 스캐폴딩, 스킬/훅, 오케스트레이션 — 의 부재에서 기인합니다. 이 코스는 세 계층을 직접 구현하면서 패턴을 해결하는 역량을 키웁니다.

### 왜 경력 데이터 분석가에게 지금 필요한가

SQL, dbt, Python을 이미 잘 다루는 경력 분석가라면, 에이전트 도구를 도입했을 때 다음 질문이 생깁니다:

- "에이전트가 내 팀의 규칙을 어떻게 알게 하지?"
- "에이전트가 비용을 초과하지 않도록 어떻게 제어하지?"
- "에이전트가 항상 올바른 메트릭 정의를 사용하게 하려면?"

이 질문들에 대한 답이 하니스 엔지니어링입니다. 그리고 여러분이 이미 보유한 역량 — `schema.yml` 작성, CI/CD 파이프라인 이해, Git 브랜치 전략 — 은 하니스의 각 계층과 직접 연결됩니다:

| 기존 역량 | 하니스 연결 포인트 |
|----------|--------------------|
| dbt `schema.yml` 작성 | → 스캐폴딩: 데이터 계약의 기술적 표현 |
| SQL 쿼리 최적화 경험 | → 스킬: 비용 효율적 분석 스킬 설계 |
| Git 브랜치·PR 워크플로 | → 스캐폴딩: 에이전트 작업 규약 문서화 |
| CI/CD 파이프라인 이해 | → 오케스트레이션: Actions 워크플로 설계 |
| Python 스크립트 작성 | → 스킬: marimo 노트북 자동 생성 구현 |

이 코스는 새로운 것을 처음부터 배우는 것이 아니라, **기존 역량 위에 하니스 엔지니어링 레이어를 추가**하는 과정입니다.

### 코스 구성 요약

| 모듈 | 제목 | 하니스 계층 | 핵심 질문 |
|------|------|------------|-----------|
| **모듈 0** | 오리엔테이션 | (준비) | 하니스 엔지니어링이란? 환경은 어떻게 준비하는가? |
| 모듈 1 | 훅과 settings.json | 스킬·훅 | 에이전트가 BigQuery 비용 정책을 스스로 지키게 하려면? |
| 모듈 2 | 슬래시 커맨드 | 스킬 | 반복 분석 작업을 재사용 가능한 명령으로 추상화하려면? |
| 모듈 3 | 권한과 AGENTS.md | 스캐폴딩·권한 | 에이전트가 이 레포를 어떻게 이해하고, 어디까지 접근하는가? |
| 모듈 4 | 종단간 워크플로 | 오케스트레이션 | 이슈 하나로 전체 분석 사이클을 자동화하려면? |

모듈 0은 다른 모듈과 구조가 다릅니다. 다른 모듈은 특정 하니스 계층의 구성 요소를 다루는 실습 중심이지만, 모듈 0은 **오리엔테이션** — 코스 전체에서 사용할 환경을 설정하고, 핵심 개념을 이해하는 준비 단계 — 입니다.

### 실습 프로젝트: FitTrack DAU/MAU 분석

코스 전체에서 동일한 실습 프로젝트를 사용합니다.

**FitTrack** — B2C 피트니스 모바일 앱의 사용자 참여도 분석

| 항목 | 내용 |
|------|------|
| 분석 목표 | DAU(일간 활성 사용자), MAU(월간 활성 사용자), 코호트 리텐션 추적 |
| 데이터 | 합성 이벤트 데이터 (~50만 건/분기), 사용자 프로필 (~1만 명) |
| 데이터 스택 | BigQuery (on-demand) + dbt + marimo |
| 자동화 스택 | GitHub Issues → GitHub Actions → Claude Agent SDK → PR |

> **왜 합성 데이터인가?** 프라이버시 보호, 완전한 재현성, 비용 예측 가능성 때문입니다. 실제 사용자 데이터 없이도 동일한 통계적 특성을 재현하도록 설계했으며, 누구나 동일한 실습 결과를 기대할 수 있습니다.

> **BigQuery 비용**: 이 코스의 실습 범위에서 BigQuery on-demand 비용은 수강생 1인당 **약 $1~5** 수준입니다. 합성 데이터가 소규모로 설계되어 있으며, 모듈 1에서 비용 제어 훅을 직접 구현합니다.

---

## 설치

이 섹션에서는 코스 전체에서 사용할 로컬 개발 환경을 구성합니다. 아래 단계를 **순서대로** 진행하세요. 각 단계 마지막의 검증 명령어로 정상 완료 여부를 확인하세요.

### 사전 요구사항 확인

설치를 시작하기 전에 다음 계정과 구독이 준비되어 있어야 합니다.

| 항목 | 필요 이유 | 준비 방법 |
|------|-----------|-----------|
| **Claude Code Pro/Max 구독** | Claude Code CLI 및 Agent SDK 사용에 필수 | [claude.ai/code](https://claude.ai/code) 에서 구독 |
| **GitHub 계정** | 레포 포크·클론, Actions, Issues | [github.com](https://github.com) |
| **GCP 계정** | BigQuery 접근 (on-demand 과금) | [cloud.google.com](https://cloud.google.com) — 신규 계정 $300 크레딧 제공 |
| **macOS 또는 Linux** | CLI 명령어 실행 환경 | Windows는 WSL2로 지원 |

> **수업 참여자에게**: 최소 3일 전에 위 항목을 준비하세요. 당일 GCP 계정·프로젝트 생성은 진행 지연의 가장 흔한 원인입니다.

---

### 단계 1: 스타터 레포 클론

```bash
# 스타터 레포 클론 (URL은 코스 자료 참조)
git clone <starter-repo-url> fittrack-analysis
cd fittrack-analysis
```

클론 후 디렉토리 구조를 확인합니다:

```
fittrack-analysis/
├── .claude/           ← Claude Code 하니스 구성 디렉토리 (현재 비어 있음)
│   ├── commands/      ← 슬래시 커맨드 파일 위치 (모듈 2에서 채움)
│   └── hooks/         ← 훅 스크립트 위치 (모듈 1에서 채움)
├── .github/
│   ├── workflows/     ← GitHub Actions 워크플로 (모듈 4에서 작성)
│   └── ISSUE_TEMPLATE/
├── models/            ← dbt 모델 (스타터 레포에 완성본 포함)
│   ├── staging/
│   └── marts/
├── notebooks/         ← marimo 분석 노트북
├── scripts/           ← 합성 데이터 생성·적재 스크립트
├── setup.sh           ← 로컬 환경 자동 설정 스크립트
└── pyproject.toml
```

> **`.claude/` 디렉토리 주목**: 지금은 비어 있습니다. 모듈 1~4를 진행하며 이 디렉토리에 하니스 구성 파일들을 추가합니다. 이 디렉토리의 변화가 여러분이 구축하는 하니스입니다.

---

### 단계 2: 로컬 도구 설치 (`setup.sh`)

```bash
# 실행 권한 확인 후 실행
chmod +x setup.sh
./setup.sh
```

`setup.sh`는 다음 도구를 순서대로 설치합니다:

| 도구 | 버전 기준 | 용도 |
|------|-----------|------|
| **uv** | 최신 안정 버전 | Python 패키지 관리자 (pip 대체) |
| **dbt-bigquery** | `pyproject.toml` 기준 | 데이터 변환 (BigQuery 어댑터 포함) |
| **marimo** | `pyproject.toml` 기준 | 분석 노트북 (Jupyter 대체) |
| **Claude Code CLI** | 최신 안정 버전 | 에이전트 인터페이스 |

설치 완료 후 각 도구의 버전을 확인합니다:

```bash
# 각 도구 버전 확인 — 네 명령 모두 버전 번호가 출력되어야 합니다
claude --version   # 예: claude 1.x.x
uv --version       # 예: uv 0.x.x
dbt --version      # 예: dbt-core 1.x.x, dbt-bigquery x.x.x
marimo --version   # 예: marimo 0.x.x
```

**성공 기준**: 네 명령 모두 오류 없이 버전 번호 출력
**실패 시**: `setup.sh` 마지막 출력에서 오류 메시지 확인 → `references/troubleshooting.md` 참조

---

### 단계 3: GCP 서비스 계정 설정

BigQuery 접근을 위한 GCP 서비스 계정을 생성하고 인증 키를 등록합니다.

#### 3-1. GCP 프로젝트 및 서비스 계정 생성

```bash
# GCP CLI 인증 (브라우저 인증 창이 열립니다)
gcloud auth login

# 프로젝트 생성 (이미 프로젝트가 있으면 스킵)
gcloud projects create fittrack-analysis-<your-id> \
  --name="FitTrack Analysis"

# 프로젝트 설정
gcloud config set project fittrack-analysis-<your-id>

# BigQuery API 활성화
gcloud services enable bigquery.googleapis.com

# 서비스 계정 생성
gcloud iam service-accounts create fittrack-agent \
  --display-name="FitTrack Agent Service Account"

# BigQuery 데이터 편집자 권한 부여 (테이블 읽기+쓰기 필요)
gcloud projects add-iam-policy-binding fittrack-analysis-<your-id> \
  --member="serviceAccount:fittrack-agent@fittrack-analysis-<your-id>.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# BigQuery 잡 실행 권한 부여 (쿼리 실행에 필요)
gcloud projects add-iam-policy-binding fittrack-analysis-<your-id> \
  --member="serviceAccount:fittrack-agent@fittrack-analysis-<your-id>.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

> **권한 설명**: `dataEditor`는 테이블 생성·수정에 필요하고, `jobUser`는 쿼리 실행에 필요합니다. dbt의 `run` 명령은 두 권한 모두 사용합니다. `dataViewer`만 부여하면 `dbt run` 시 테이블 생성 권한 오류가 발생합니다.

#### 3-2. JSON 키 파일 생성

```bash
# JSON 키 생성 (이 파일은 비밀 정보입니다 — 레포에 절대 커밋하지 마세요)
gcloud iam service-accounts keys create /tmp/fittrack-sa-key.json \
  --iam-account=fittrack-agent@fittrack-analysis-<your-id>.iam.gserviceaccount.com
```

#### 3-3. GitHub Secrets 등록

```bash
# GitHub CLI로 Secrets 등록 (gh auth login이 선행되어야 합니다)

# GCP 서비스 계정 JSON 키 (파일 내용 전체를 Secret으로 등록)
gh secret set GCP_SA_KEY < /tmp/fittrack-sa-key.json

# GCP 프로젝트 ID
gh secret set GCP_PROJECT_ID --body "fittrack-analysis-<your-id>"

# 등록 확인 (값은 마스킹되어 표시됩니다)
gh secret list
```

**성공 기준**: `gh secret list` 출력에 `GCP_SA_KEY`, `GCP_PROJECT_ID`가 표시됨

> **보안 주의**: `/tmp/fittrack-sa-key.json`은 등록 후 삭제하세요: `rm /tmp/fittrack-sa-key.json`
> 상세 가이드: `references/gcp-bigquery-setup.md` 참조

---

### 단계 4: GitHub 인증 설정

GitHub Actions에서 브랜치 생성, PR 생성 등의 Git 작업에 사용할 인증을 설정합니다.

#### 방법 A: Personal Access Token (간단, 개인 실습 권장)

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)" 클릭
3. 스코프 선택: `repo` (전체), `workflow`
4. 생성된 토큰 복사 후 등록:

```bash
gh secret set GITHUB_PAT --body "<YOUR_PAT_TOKEN>"
```

#### 방법 B: GitHub App (팀 환경 권장)

팀 환경에서 공유하거나 보안 요구사항이 높은 경우, GitHub App을 사용합니다. 상세 설정은 `references/github-app-setup.md`를 참조하세요.

---

### 단계 5: Claude Code 인증 및 Agent SDK 토큰 등록

```bash
# Claude Code 로그인 (브라우저 인증 창이 열립니다)
claude login

# 로그인 상태 확인
claude whoami
# 예상 출력: your.email@example.com (Pro/Max 구독)

# 비대화형 모드 테스트 (GitHub Actions에서 사용하는 방식)
claude -p "숫자 1부터 5까지 출력해줘." --output-format text

# Claude 토큰을 GitHub Secret으로 등록
# (claude setup-token 명령으로 자동화 환경용 토큰 생성)
claude setup-token
# 출력된 토큰을 복사하여:
gh secret set CLAUDE_TOKEN --body "<SETUP_TOKEN_OUTPUT>"
```

**성공 기준**:
- `claude whoami` → 이메일 주소 출력
- `claude -p "..."` → 숫자 목록 출력 (오류 없음)
- `gh secret list` → `CLAUDE_TOKEN` 표시

> **토큰 만료**: Claude 토큰은 일정 기간 후 만료될 수 있습니다. 만료 시: `claude login` → `claude setup-token` → `gh secret set CLAUDE_TOKEN` 순으로 갱신하세요.
> 상세 가이드: `examples/claude-agent-sdk-setup-guide.md` 참조

---

### 단계 6: 합성 데이터 생성 및 BigQuery 적재

```bash
# 환경 변수 설정 (로컬 실행용 — Actions에서는 Secret으로 주입됨)
export GOOGLE_APPLICATION_CREDENTIALS="/tmp/fittrack-sa-key.json"
export GCP_PROJECT_ID="fittrack-analysis-<your-id>"

# 합성 데이터 생성 (로컬에 CSV 파일 생성)
uv run python scripts/generate_synthetic_data.py

# BigQuery에 적재
uv run python scripts/load_to_bigquery.py
```

생성되는 테이블:

| 테이블 | 레코드 수 (약) | 설명 | 예상 크기 |
|--------|---------------|------|-----------|
| `raw.raw_events` | 500,000건 | 2026년 1분기 앱 이벤트 로그 | ~80 MB |
| `raw.raw_users` | 10,000명 | 사용자 프로필 (가입일, 플랫폼, 등급) | ~2 MB |

> **BigQuery 비용 예상 (on-demand)**:
> - `raw_events` 전체 스캔: ~$0.40 (80MB × $5/TB)
> - 파티션 필터 적용 시 (일별): ~$0.001 (1일치 약 10MB × $5/TB)
> - 모듈 1에서 파티션 필터 강제 훅을 구현하여 비용을 90% 이상 절감합니다.

적재 완료 후 BigQuery 콘솔 또는 CLI로 확인:

```sql
-- BigQuery 콘솔에서 실행하여 적재 확인
-- 예상 비용: $0 (메타데이터 조회, 데이터 스캔 없음)
SELECT
  table_id,
  row_count,
  size_bytes / 1024 / 1024 AS size_mb
FROM `fittrack-analysis-<your-id>.raw.__TABLES__`
ORDER BY table_id;
```

---

### 단계 7: dbt 실행 및 검증

```bash
# dbt 프로파일 설정 확인 (BigQuery 연결 정보)
dbt debug

# dbt 패키지 설치 (packages.yml 의존성)
dbt deps

# 모든 모델 빌드
dbt run
# 예상 출력: "Completed successfully" — staging 2개, mart 3개 모델

# 데이터 품질 테스트 실행
dbt test
# 예상 출력: "Pass" — Fail 0건
```

`dbt run` 후 생성되는 모델:

```
models/
├── staging/
│   ├── stg_events.sql          -- 이벤트 클렌징, KST 타임존 통일
│   └── stg_users.sql           -- 사용자 프로필 정규화
└── marts/
    ├── fct_daily_active_users.sql   -- DAU 집계 (그레인: 날짜)
    ├── fct_monthly_active_users.sql -- MAU 집계 (그레인: 연-월)
    └── fct_retention_cohort.sql     -- D1/D7/D30 코호트 리텐션
```

> **dbt 비용 (BigQuery on-demand)**:
> - staging 모델 빌드: ~$0.02 (전처리 쿼리, 소량 데이터)
> - mart 모델 빌드: ~$0.05 (집계 쿼리, 파티션 활용 시)
> - `dbt test`: ~$0.01 (not_null, unique 체크)
> - **총 예상**: 첫 실행 ~$0.10 미만

**성공 기준**: `dbt run` 출력에 `ERROR 0`, `dbt test` 출력에 `FAIL 0`

**실패 시 체크리스트**:
1. `dbt debug` 출력에서 BigQuery 연결 오류 확인
2. `profiles.yml`의 `project`, `dataset`, `keyfile` 경로 확인
3. 서비스 계정에 `bigquery.dataEditor` + `bigquery.jobUser` 권한 확인
4. `references/troubleshooting.md` → "dbt 연결 오류" 섹션 참조

---

### 설치 완료 확인 요약

| # | 항목 | 검증 명령 | 성공 기준 |
|---|------|-----------|-----------|
| 1 | Claude Code CLI | `claude --version` | 버전 번호 출력 |
| 2 | uv | `uv --version` | 버전 번호 출력 |
| 3 | dbt | `dbt --version` | core 버전 + bigquery 어댑터 출력 |
| 4 | marimo | `marimo --version` | 버전 번호 출력 |
| 5 | GitHub Secrets | `gh secret list` | GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_TOKEN, GITHUB_PAT 표시 |
| 6 | BigQuery 데이터 적재 | BigQuery 콘솔 조회 | raw_events ~50만 건, raw_users ~1만 명 |
| 7 | dbt 모델 빌드 | `dbt run && dbt test` | ERROR 0, FAIL 0 |

모든 항목이 성공 기준을 충족하면 모듈 1로 진행할 준비가 된 것입니다.

---

## 개념 소개

이 섹션은 코스 전체에서 반복적으로 등장하는 핵심 개념을 처음으로 소개합니다. 모듈 1~4를 진행하며 이 개념들이 구체적인 코드와 연결될 때마다 이 섹션을 참조하세요.

> **용어 표기 원칙**: 한국어 공식 표준이 없는 개념은 처음 등장 시 **한국어 용어 (English original)** 형식으로 표기합니다. 이후 사용 시 한국어 용어를 우선합니다.

---

### Claude Code 아키텍처

**Claude Code**는 Anthropic이 개발한 코딩 에이전트입니다. 터미널(대화형)과 자동화 환경(비대화형) 두 가지 모드로 실행됩니다.

```
┌──────────────────────────────────────────────────────────┐
│                   Claude Code 실행 모드                   │
├──────────────────────────┬───────────────────────────────┤
│  대화형 (Interactive)    │  비대화형 (Non-interactive)    │
│  터미널에서 직접 실행    │  GitHub Actions에서 자동 실행  │
│  사람이 응답 검토·승인   │  claude -p "..." 플래그 사용  │
│  모듈 0~2 주 사용 모드   │  모듈 4 자동화의 핵심 모드    │
└──────────────────────────┴───────────────────────────────┘
```

Claude Code는 작업을 실행할 때 다음 흐름을 따릅니다:

```
사용자 명령 (또는 자동화 트리거)
      ↓
[문맥 구성]
AGENTS.md + settings.json + 레포 파일 트리 읽기
      ↓
[계획 수립]
언어 모델이 작업 계획 생성
      ↓
[도구 실행 루프]  ← 이 루프가 반복되며 작업 수행
  ┌── PreToolUse 훅 실행 (예: BigQuery 비용 사전 점검)
  │   도구 실행 (Bash, Read, Write, Edit 등)
  │   PostToolUse 훅 실행 (예: dbt 자동 테스트)
  └── 결과를 문맥에 추가 후 다음 단계 결정
      ↓
[완료]
Stop 훅 실행 (예: 실행 요약 로그 기록)
```

**하니스는 이 흐름의 각 단계에 개입합니다.** 문맥 구성(AGENTS.md), 실행 정책(settings.json), 도구 실행 전후(훅), 명령 범위(permissions)가 모두 하니스의 구성 요소입니다.

---

### 하니스의 세 계층

하니스(harness)는 Claude Code가 안전하고 일관되게 작업을 수행하도록 돕는 **환경 전체**입니다. 레포지토리 구조, 문서, 정책, 피드백 루프, 자동화 파이프라인을 포함합니다.

하니스는 세 계층으로 구성됩니다:

```
┌────────────────────────────────────────────────────────┐
│         계층 3: 오케스트레이션 (Orchestration)          │
│   GitHub Actions + Claude Agent SDK                   │
│   "언제, 어떤 순서로, 어떤 조건에서 에이전트를 실행?"  │
├────────────────────────────────────────────────────────┤
│           계층 2: 스킬과 훅 (Skills & Hooks)           │
│   Claude Code 슬래시 커맨드 + settings.json 훅         │
│   "에이전트가 무엇을 할 수 있고, 어떤 규칙을 따르는가?" │
├────────────────────────────────────────────────────────┤
│           계층 1: 스캐폴딩 (Scaffolding)               │
│   AGENTS.md + 데이터 계약 + Issue 템플릿               │
│   "에이전트가 이 레포를 어떻게 이해하는가?"             │
└────────────────────────────────────────────────────────┘
              ↕ 아래 계층 없이 위 계층은 작동하지 않음
```

**계층 1 — 스캐폴딩 (scaffolding)**: 에이전트가 레포지토리를 정확히 이해하도록 돕는 문서와 구조입니다. `AGENTS.md`는 레포 규칙과 규약을 선언하고, 데이터 계약은 테이블의 의미를 코드로 정의하며, Issue 템플릿은 분석 요청의 입력 스키마 역할을 합니다. *모듈 3에서 구현합니다.*

**계층 2 — 스킬과 훅 (skill / hook)**: 에이전트가 수행할 수 있는 작업(스킬)과 자동으로 실행되는 정책(훅)을 정의합니다. 슬래시 커맨드로 분석 작업을 명세화하고, 훅으로 비용·검증 정책을 코드로 강제합니다. *모듈 1(훅)과 모듈 2(슬래시 커맨드)에서 구현합니다.*

**계층 3 — 오케스트레이션 (orchestration)**: GitHub Actions와 Claude Agent SDK를 사용하여 에이전트를 이슈 기반으로 자동 실행합니다. 사람이 GitHub Issue를 열면 → Actions가 에이전트를 실행하고 → 에이전트가 분석을 수행하고 → PR을 생성하는 전체 흐름을 자동화합니다. *모듈 4에서 구현합니다.*

---

### Claude Code의 다섯 가지 구성 요소

Claude Code를 하니스로 제어하는 다섯 가지 구성 요소를 소개합니다. 이 코스에서 구현하는 모든 하니스 코드는 이 다섯 요소 중 하나에 속합니다.

#### ① AGENTS.md — 에이전트 문맥 파일 (agent context file)

Claude Code가 레포지토리를 처음 열면 `AGENTS.md` 파일을 자동으로 읽습니다. 에이전트에게 "이 레포에서 어떻게 일해야 하는가"를 선언하는 문서입니다.

```markdown
# AGENTS.md 구성 예시 (모듈 3에서 직접 작성합니다)

## 레포 개요
FitTrack 모바일 앱의 DAU/MAU 분석 레포입니다.

## 데이터 레이어 규칙
- mart 레이어(fct_*)만 최종 메트릭 소스로 사용할 것
- staging 레이어(stg_*)는 직접 쿼리하지 말 것

## 작업 규약
- 브랜치명: analysis/<issue-number>-<slug>
- 커밋: 분석 결과물만 커밋 (원시 데이터 파일 제외)

## BigQuery 비용 정책
- 모든 쿼리에 파티션 필터(event_date) 사용 필수
- 스캔 예상 비용이 $1를 초과하면 실행 전 명시적 승인 요청
```

*⚠️ 모듈 0에서는 아직 `AGENTS.md`가 없습니다. 모듈 3에서 직접 작성합니다. 지금 이 구조를 머릿속에 담아두세요.*

#### ② settings.json — 에이전트 실행 정책 파일 (agent execution policy file)

`.claude/settings.json`은 에이전트의 실행 정책을 JSON으로 선언하는 파일입니다. 허용 명령어(permissions), 환경 변수(env), 훅 등록(hooks)을 정의합니다.

```jsonc
// .claude/settings.json 구조 예시
// (모듈 1에서 처음 생성하고, 모듈 2~3에서 점진적으로 확장합니다)
{
  // 에이전트가 실행할 수 있는 명령어 범위 선언
  "permissions": {
    // 명시적으로 허용할 Bash 명령어 패턴
    "allow": [
      "Bash(dbt run*)",         // dbt 모델 빌드 허용
      "Bash(dbt test*)",        // dbt 테스트 허용
      "Bash(marimo run*)",      // marimo 노트북 실행 허용
      "Bash(bq query --dry_run*)" // BigQuery dry-run(비용 점검)만 허용
    ],
    // 명시적으로 차단할 명령어
    "deny": [
      "Bash(rm -rf*)",          // 재귀 삭제 방지
      "Bash(bq rm*)"            // BigQuery 테이블 삭제 방지
    ]
  },
  // 이벤트별 훅 스크립트 등록
  "hooks": {
    // 도구 실행 직전에 실행할 훅
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            // BigQuery 쿼리 비용 사전 점검 훅 (모듈 1에서 작성)
            "command": ".claude/hooks/bq-cost-guard.sh"
          }
        ]
      }
    ]
  }
}
```

*⚠️ 모듈 0에서는 아직 `settings.json`이 없습니다. 모듈 1에서 처음 생성합니다.*

#### ③ 슬래시 커맨드 — 재사용 가능한 에이전트 작업 (slash command)

`.claude/commands/` 디렉토리의 `.md` 파일로 정의되는 커스텀 슬래시 커맨드(slash command)는, 반복 분석 작업을 에이전트에게 명령할 때 사용하는 재사용 가능한 프롬프트 템플릿입니다.

```
# 이 코스에서 구현할 슬래시 커맨드 목록 (모듈 2에서 작성)
/analyze         → Issue 번호를 받아 분석 실행
/validate        → dbt 모델 컴파일 및 테스트 자동 실행
/generate-report → marimo 노트북으로 리포트 생성
/check-cost      → BigQuery 쿼리 예상 비용 사전 점검
```

*⚠️ 모듈 0에서는 아직 커맨드 파일이 없습니다. 모듈 2에서 직접 작성합니다.*

#### ④ 훅 — 이벤트 기반 자동 정책 (event-driven automatic policy)

훅(hook)은 Claude Code의 특정 이벤트(도구 실행 전후, 에이전트 완료 시)에 자동으로 실행되는 쉘 스크립트입니다. 에이전트에게 프롬프트로 규칙을 지시하는 것과 달리, 훅은 **시스템 수준에서 정책을 강제**합니다.

```
이벤트 유형          언제 실행되는가               이 코스 사용 예
─────────────────────────────────────────────────────────────────────
PreToolUse     도구 실행 직전            BigQuery 비용 사전 점검 훅
PostToolUse    도구 실행 직후            dbt 모델 변경 시 자동 테스트 훅
Stop           에이전트 응답 완료 시     실행 결과 요약 로그 기록 훅
```

> **왜 훅이 프롬프트보다 강력한가?** 프롬프트로 "BigQuery 전체 테이블 스캔하지 마세요"라고 지시해도, 에이전트는 상황에 따라 이를 무시하거나 잊을 수 있습니다. 훅은 에이전트가 실제로 명령을 실행하기 **직전**에 개입하여 비용을 점검하고, 임계값 초과 시 실행을 중단합니다. 이 차이가 하니스 엔지니어링의 핵심입니다.

#### ⑤ Permissions — 도구 접근 제어 (tool access control)

Permissions(권한)는 에이전트가 실행할 수 있는 시스템 명령어의 범위를 화이트리스트/블랙리스트로 제어합니다. `allow` 목록에 없는 명령어를 에이전트가 실행하려 하면 사람에게 확인을 요청하거나 실행을 차단합니다.

이것은 단순한 보안 기능이 아닙니다. 에이전트가 실수로 데이터를 삭제하거나, 예상치 못한 외부 API를 호출하거나, 과도한 BigQuery 비용을 유발하는 상황을 **시스템 수준에서 방지하는 하니스의 핵심 메커니즘**입니다.

---

### 하니스 구성 요소와 모듈 매핑

| Claude Code 구성 요소 | 하니스 계층 | 구현 모듈 | 역할 |
|----------------------|------------|-----------|------|
| `AGENTS.md` | 스캐폴딩 | 모듈 3 | 에이전트가 레포를 이해하는 기준 |
| `settings.json` (훅) | 스킬·훅 | 모듈 1 | 이벤트 기반 자동 정책 실행 |
| `.claude/commands/*.md` | 스킬 | 모듈 2 | 재사용 가능한 분석 작업 명세 |
| `settings.json` (permissions) | 권한 제어 | 모듈 3 | 실행 가능 명령어 범위 설정 |
| Claude Agent SDK (`claude -p`) | 오케스트레이션 | 모듈 4 | 비대화형 자동 실행 |

---

### 핵심 용어 사전

이 코스에서 반복적으로 사용하는 용어를 정리합니다. 각 용어의 한국어 명칭은 아래와 같이 정립합니다.

| 한국어 용어 | 영어 원어 | 정의 |
|------------|----------|------|
| **하니스** | harness | 에이전트가 안전·일관되게 작동하도록 돕는 환경 전체 |
| **스캐폴딩** | scaffolding | 에이전트가 레포를 이해하도록 돕는 문서와 구조 |
| **스킬** | skill | 에이전트가 수행할 수 있는 재사용 가능한 작업 단위 |
| **훅** | hook | 특정 이벤트에 자동으로 실행되는 쉘 스크립트 정책 |
| **오케스트레이션** | orchestration | 에이전트의 실행 흐름을 자동화하는 시스템 |
| **에이전트 문맥 파일** | agent context file | 에이전트가 레포 시작 시 자동으로 읽는 지침 파일 (AGENTS.md) |
| **실행 정책 파일** | execution policy file | 에이전트 실행 규칙을 JSON으로 선언한 파일 (settings.json) |
| **슬래시 커맨드** | slash command | `.claude/commands/`의 재사용 가능한 프롬프트 템플릿 |
| **도구 접근 제어** | tool access control | allow/deny로 에이전트 실행 가능 명령어 범위 설정 |
| **데이터 계약** | data contract | 테이블의 소유자·그레인·스키마·신선도를 코드로 선언한 것 |
| **완료 증거** | completion evidence | 에이전트 작업 완료를 기계적으로 검증하는 기준 |
| **파이프라인 산출물** | pipeline output | 하니스가 구동하는 에이전트가 생성하는 결과물 |

---

### Claude Code를 활용한 프로젝트 탐색 (선택 실습)

설치가 완료된 후, Claude Code를 대화형으로 실행하여 프로젝트 구조를 탐색해 보세요. 이 실습은 하니스 없이 에이전트가 어떻게 작동하는지 기준선(baseline)을 측정하는 데 목적이 있습니다.

```bash
# 대화형 Claude Code 실행
claude

# 또는 단일 프롬프트로 실행
claude "이 dbt 프로젝트의 데이터 흐름을 설명해줘.
sources.yml의 소스 테이블에서 시작하여 staging 모델을 거쳐
mart 모델(fct_daily_active_users, fct_monthly_active_users)까지의
변환 과정을 단계별로 정리해줘.
각 모델의 그레인(grain)과 주요 컬럼도 포함해줘."
```

**관찰 포인트**: 에이전트가 어떤 파일을 읽는가? 메트릭 정의를 어디서 가져오는가? 답변에서 빠진 정보는 무엇인가?

모듈 3에서 `AGENTS.md`를 추가한 후 같은 질문을 하면, **응답 품질의 차이**를 직접 확인할 수 있습니다. 이 비교가 스캐폴딩의 필요성을 체감하는 핵심 학습 경험입니다.

---

## 자기 점검 체크리스트

모듈 0을 완료한 후 아래 체크리스트를 확인하세요. 각 항목에 **합격(PASS)** 또는 **불합격(FAIL)** 기준을 명시합니다.

### 설치 완료 점검

- [ ] **`claude --version` 실행 시 버전이 출력되는가?**
  - PASS: 버전 번호가 출력됨 (예: `claude 1.x.x`)
  - FAIL: 명령어를 찾을 수 없음 또는 오류 → `npm install -g @anthropic-ai/claude-code` 수동 실행

- [ ] **`dbt run` 실행 시 모든 모델이 성공적으로 빌드되는가?**
  - PASS: 출력에 `Completed successfully`, `ERROR 0`
  - FAIL: 오류 있음 → `dbt debug` 실행 후 연결 오류 확인, `profiles.yml` 검토

- [ ] **`dbt test` 실행 시 모든 테스트가 통과하는가?**
  - PASS: 출력에 `FAIL 0`
  - FAIL: 실패한 테스트 이름 확인 → 합성 데이터 적재 스크립트 재실행 또는 데이터 무결성 검토

- [ ] **BigQuery 콘솔에서 `raw_events` 테이블 조회 시 약 50만 건이 나오는가?**
  - PASS: `SELECT COUNT(*) FROM raw.raw_events` → 결과 400,000~600,000 범위
  - FAIL: 0건 또는 오류 → `scripts/load_to_bigquery.py` 재실행, GCP 인증 확인

- [ ] **`gh secret list`에 필수 4개 Secret이 모두 표시되는가?**
  - PASS: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, `GITHUB_PAT`(또는 `APP_ID`+`APP_PRIVATE_KEY`) 표시
  - FAIL: 누락된 Secret 있음 → GitHub UI > Settings > Secrets > Actions에서 수동 등록

### 개념 이해 점검

- [ ] **하니스 엔지니어링의 세 계층을 설명할 수 있는가?**
  - PASS: "스캐폴딩은 에이전트가 레포를 이해하도록 돕는다 / 스킬·훅은 에이전트가 규칙을 따르도록 강제한다 / 오케스트레이션은 에이전트를 자동으로 실행한다"를 각각 연결할 수 있음
  - FAIL: 세 계층을 구분하지 못하거나, 계층 간 의존 관계를 설명하지 못함 → 이 모듈의 [개념 소개] 섹션 재독

- [ ] **하니스와 파이프라인 산출물의 차이를 설명할 수 있는가?**
  - PASS: "내가 만드는 것은 하니스(settings.json, 훅 스크립트, AGENTS.md), 에이전트가 만드는 것은 산출물(BigQuery 분석 결과, dbt 모델, marimo 리포트)"을 구분할 수 있음
  - FAIL: 이 구분이 불명확함 → [개요] 섹션의 "두 가지 혼동을 피하세요" 재독

- [ ] **`settings.json`의 `permissions`, `hooks` 구조의 역할을 설명할 수 있는가?**
  - PASS: `permissions`는 실행 가능한 명령어 범위를 선언하고, `hooks`는 이벤트별로 실행할 스크립트를 등록한다는 것을 설명할 수 있음
  - FAIL: 아직 개념이 불명확해도 괜찮습니다 — 모듈 1에서 직접 작성하며 이해합니다

### 모듈 0 완료 기준

위 체크리스트에서:
- **설치 완료 점검 5개 항목 모두 PASS** → 모듈 1 진행 가능
- **개념 이해 점검 3개 항목 모두 PASS** → 이상적 상태 (모듈 1에서 개념이 더 명확해집니다)
- **설치 항목에 FAIL이 있음** → 모듈 1 진행 전에 반드시 해결 필요

---

## 강사 노트

### 모듈 0의 특별한 위치

모듈 0은 다른 모듈과 다른 구조를 가집니다. 다른 모듈은 특정 하니스 계층을 구현하는 실습이 중심이지만, 모듈 0은 순수한 오리엔테이션입니다. 이 차이를 수강생에게 명확히 전달하세요:

- 모듈 0: 환경 준비 + 개념 지도 형성
- 모듈 1~4: 하니스 계층을 코드로 구현하는 실습

### 시간 배분 가이드

| 활동 | 예상 시간 | 유의사항 |
|------|-----------|---------|
| 개요 섹션 읽기 및 강의 | 25분 | 시나리오 1~3을 경험담으로 풀어내면 공감도 높음 |
| 설치 단계 1~2 (레포 클론, `setup.sh`) | 15분 | 네트워크 상태에 따라 편차 큼 |
| 설치 단계 3~5 (GCP, GitHub, Claude 인증) | 25분 | **가장 지연되기 쉬운 구간** — 사전 안내 필수 |
| 설치 단계 6~7 (데이터 적재, dbt 실행) | 15분 | GCP 설정 완료 후 진행 가능 |
| 개념 소개 섹션 및 Q&A | 15분 | 용어 정리에 집중, 구현은 모듈 1~4에서 |
| **총계** | **1.5~2시간** | GCP 이슈 시 2.5시간까지 연장 가능 |

### 사전 안내 (수업 최소 3일 전)

수강생에게 사전 이메일로 안내하세요:
1. Claude Code Pro/Max 구독 확인
2. GCP 프로젝트 생성 및 결제 계정 연결
3. GitHub 계정 및 `gh` CLI 설치 확인
4. macOS: Xcode Command Line Tools 설치 (`xcode-select --install`)

당일 GCP 계정·프로젝트 생성은 진행 지연의 가장 흔한 원인입니다.

### 수강생 흔한 실수

1. **GCP 권한 부족**: `bigquery.dataViewer`만 부여하고 `dataEditor`를 빠트리는 경우. `dbt run`에서 테이블 생성 권한 오류 발생 → 권한 확인 후 `dataEditor` 추가.

2. **GitHub Secret에 따옴표 포함**: JSON 키를 텍스트로 복사할 때 불필요한 따옴표가 추가됨. `gh secret set GCP_SA_KEY < key.json` 방식 (파일에서 직접 읽기) 권장.

3. **Claude 비대화형 모드 실패**: `claude --version`은 성공하지만 `claude -p "..."` 실행 시 인증 오류. `claude login` 실행 후 다시 시도.

4. **profiles.yml 경로 오류**: dbt가 기본적으로 `~/.dbt/profiles.yml`을 읽는데, 레포에 `profiles.yml`을 만들어도 자동으로 읽히지 않음. `--profiles-dir .` 플래그 또는 환경 변수 `DBT_PROFILES_DIR=.` 사용.

### "왜 Jupyter가 아닌 marimo인가?" 대비

경력 분석가들은 marimo에 익숙하지 않을 수 있습니다. 간단히 설명:
- marimo는 셀 간 의존성을 자동으로 추적하여 재현 가능한 노트북을 보장합니다
- `.py` 파일로 저장되어 Git 관리가 명확합니다
- HTML 정적 리포트 내보내기가 내장되어 있습니다
- 에이전트가 노트북을 자동 생성할 때 셀 순서 문제가 발생하지 않습니다
