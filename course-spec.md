# 하니스 엔지니어링 for 데이터 분석

> Claude Code와 GitHub Actions를 활용한 에이전트 기반 데이터 분석 자동화 코스

---

## 목차

1. [코스 개요](#코스-개요)
2. [하니스 엔지니어링이란?](#하니스-엔지니어링이란)
3. [수강 대상 및 사전 요구사항](#수강-대상-및-사전-요구사항)
4. [코스 구조](#코스-구조)
5. [학습 목표](#학습-목표)
6. [모듈 구성](#모듈-구성)
   - [모듈 0: 환경 설정 및 프로젝트 이해](#모듈-0-환경-설정-및-프로젝트-이해)
   - [모듈 1: 훅과 설정 엔지니어링](#모듈-1-훅과-설정-엔지니어링--settingsjson으로-에이전트-정책-구현)
   - [모듈 2: 슬래시 커맨드 작성](#모듈-2-슬래시-커맨드-작성--에이전트-작업-명세화)
   - [모듈 3: 권한 오케스트레이션](#모듈-3-권한-오케스트레이션--claude-code-권한-정책으로-에이전트-경계-설계)
   - [모듈 4: 종단간 에이전트 기반 데이터 분석 워크플로](#모듈-4-종단간-에이전트-기반-데이터-분석-워크플로--하니스-전체-통합-및-실행)
7. [모듈 간 학습 흐름](#모듈-간-학습-흐름)
8. [샘플 프로젝트 상세](#샘플-프로젝트-상세-모바일-앱-dauMAU-분석)
9. [평가 기준](#평가-기준)
10. [교수자/운영자 참고사항](#교수자운영자-참고사항)
11. [용어 정리](#용어-정리)
12. [참고 자료](#참고-자료)

---

## 코스 개요

이 코스는 **하니스 엔지니어링(harness engineering)** 개념을 데이터 분석 워크플로에 적용하는 방법을 다룹니다. 수강생은 Claude Code를 데이터 분석 에이전트로 활용하기 위해 레포지토리를 어떻게 설계해야 하는지 — **스캐폴딩(scaffolding)**, **스킬(skill)**/**훅(hook)**, **오케스트레이션(orchestration)**의 세 계층을 직접 구축하며 배웁니다.

**핵심 전제**: 코딩 에이전트의 성능은 모델 능력만으로 결정되지 않습니다. 에이전트가 작업하는 레포지토리의 구조, 정책, 피드백 루프가 결과 품질을 좌우합니다. 이 코스에서는 "에이전트가 안전하고 일관되게 분석 작업을 수행할 수 있는 환경"을 설계하는 엔지니어링 역량을 길러냅니다.

### 샘플 프로젝트

B2C 모바일 앱의 **DAU(일간 활성 사용자) / MAU(월간 활성 사용자)** 분석을 실습 프로젝트로 사용합니다. 수강생은 BigQuery에 적재된 합성 이벤트 데이터를 dbt로 변환하고, marimo 노트북으로 분석 리포트를 생성하며, 이 전체 과정을 Claude Code 에이전트가 자동으로 수행하도록 하니스를 구축합니다.

---

## 하니스 엔지니어링이란?

"하니스(harness)"라는 개념은 두 가지 차원에서 이해해야 합니다.

**하니스-파일(harness as files)**: 레포지토리에 존재하는 정적 설정 파일들을 말합니다. `settings.json`, 훅(hook) 정의, `AGENTS.md`, 슬래시 커맨드(`commands/*.md`), GitHub Actions 워크플로 등이 여기에 해당합니다. 이 파일들은 에이전트가 어떻게 행동해야 하는지를 *선언*합니다.

**하니스-시스템(harness as emergent behavior)**: 위의 파일들이 에이전트 런타임에서 함께 작동할 때 *창발*하는 동적 행동 체계를 말합니다. 개별 파일의 내용을 아는 것만으로는 충분하지 않습니다 — 파일들이 서로 상호작용하며 에이전트의 실제 행동을 결정하는 방식을 이해해야 합니다.

### 왜 이 구분이 중요한가?

수강생은 두 가지 역량을 모두 갖춰야 합니다:

1. **파일을 올바르게 구성하는 능력** — 각 설정 파일의 문법, 위치, 옵션을 정확히 알고 작성할 수 있어야 합니다.
2. **시스템 수준에서 추론하는 능력** — 여러 파일이 동시에 활성화되었을 때 에이전트가 어떻게 행동할지 예측할 수 있어야 합니다.

파일만 잘 작성해도 시스템이 의도대로 작동하지 않을 수 있고, 반대로 시스템 동작을 이해하면 파일을 더 효과적으로 설계할 수 있습니다.

### 하니스의 두 차원

```
하니스-파일 (정적)          하니스-시스템 (동적)
├── AGENTS.md              ├── 에이전트가 규칙을 읽고 따름
├── settings.json          ├── 훅이 자동으로 실행됨
├── commands/*.md          ├── 스킬이 호출 가능해짐
├── .github/workflows/     ├── 이슈 라벨로 워크플로 트리거
└── dbt 모델/테스트         └── 데이터 품질이 기계적으로 검증됨
```

### 모듈별 초점

- **모듈 1–2**: 하니스-파일에 집중합니다. 개별 설정 파일을 올바르게 작성하고 구성하는 방법을 배웁니다.
- **모듈 3**: 하니스-시스템에 집중합니다. 파일들이 런타임에서 어떻게 상호작용하는지, 권한 경계와 실행 흐름을 설계하는 방법을 배웁니다.
- **모듈 4**: 하니스-파일과 하니스-시스템 모두를 유지보수합니다. 종단간 워크플로를 통해 두 차원을 통합하고 지속적으로 관리하는 역량을 기릅니다.

### 용어 정의

**하니스 엔지니어링(harness engineering)**은 OpenAI가 2026년에 제안한 용어의 음차 표기입니다. 코딩 에이전트가 효과적으로 작동할 수 있도록 레포지토리 환경을 설계하는 엔지니어링 분야를 가리킵니다.

아직 정립된 한국어 대응어는 없습니다. "에이전트 환경 설계", "에이전트 구성 공학" 등으로 의역할 수 있으나, 이 코스에서는 에이전트 퍼스트 개발에 고유한 기술 용어로서 **하니스**를 그대로 사용합니다.

**주요 용어 정리:**

| 용어 | 원어 | 설명 |
|------|------|------|
| 스캐폴딩 | scaffolding | 에이전트가 작업을 시작하기 전에 갖춰야 할 기본 구조 (디렉터리 구성, 설정 파일 배치 등) |
| 훅 | hook | 에이전트의 특정 동작 전후에 자동으로 실행되는 검증/변환 로직 |
| 스킬 | skill | 슬래시 커맨드로 호출 가능한 재사용 가능한 작업 명세 |
| 오케스트레이션 | orchestration | 여러 에이전트 동작, 훅, 워크플로를 조율하여 전체 파이프라인이 일관되게 작동하도록 하는 것 |

---

## 수강 대상 및 사전 요구사항

### 대상

SQL, dbt, Python을 실무에서 사용하는 **경력 데이터 분석가**

### 사전 요구사항

| 영역 | 요구 수준 |
|------|-----------|
| SQL | BigQuery 또는 유사 DW에서 집계, 윈도우 함수, CTE를 활용한 쿼리 작성 가능 |
| dbt | source → staging → mart 모델 구조 이해, `dbt run` / `dbt test` 경험 |
| Python | pandas, 기본 시각화 라이브러리 사용 경험, uv/pip 패키지 관리 이해 |
| Git/GitHub | 브랜치, PR, merge 워크플로 이해 |
| 터미널 | macOS/Linux 터미널에서 CLI 명령어 실행 가능 |

### 필수 구독/계정

- **Claude Code Pro 또는 Max 구독** (Claude Code CLI 사용에 필요)
- GitHub 계정 (GitHub Actions 사용)
- GCP 계정 (BigQuery 접근, on-demand 가격 — 실습 범위 내 비용 최소)

---

## 코스 구조

### 기본 정보

| 항목 | 내용 |
|------|------|
| 총 기간 | 2~4주 |
| 주당 학습 시간 | 2~3시간 |
| 총 학습 시간 | 4~12시간 (개인 속도에 따라 조절) |
| 언어 정책 | 코스 문서: 한국어 / 코드 변수·함수명: 영어 / 코드 주석·설명: 한국어 |
| 평가 방식 | 모듈별 자기 점검 체크리스트 (캡스톤 없음) |

### 기술 스택

| 계층 | 도구 | 용도 |
|------|------|------|
| 데이터 웨어하우스 | BigQuery (on-demand) | 합성 이벤트 데이터 저장 |
| 데이터 변환 | dbt + MetricFlow | source → staging → mart 모델, 시맨틱 레이어 |
| 분석 노트북 | marimo | 로컬 Python 노트북, HTML/PDF 정적 리포트 내보내기 |
| 이슈 관리 | GitHub Issues | 분석 요청·추적 (Linear 미사용) |
| CI/CD·오케스트레이션 | GitHub Actions | 라벨 트리거 워크플로, 자동화 파이프라인 |
| 에이전트 | Claude Code + Claude Agent SDK | 분석 작업 실행, `claude setup-token` 기반 자동화 |
| 로컬 환경 | Python / uv | 패키지 관리, 로컬 개발 환경 |
| 인증 | GCP 서비스 계정 JSON (GitHub Secret) | BigQuery 인증 |
| Git 인증 | PAT 또는 GitHub App (GitHub Secret) | GitHub Actions 내 Git 작업 인증 |

### 스타터 레포지토리 구성

스타터 레포에는 다음이 **포함됩니다**:

- dbt 프로젝트: 완성된 mart 모델 (DAU/MAU 집계)
- 합성 이벤트 데이터 생성 스크립트
- 로컬 환경 자동 설정 스크립트 (`setup.sh`)
- `pyproject.toml` 및 uv lock 파일

다음은 **포함되지 않습니다** (수강생이 직접 작성):

- `AGENTS.md`
- GitHub Actions 워크플로 YAML 파일
- Claude Code 스킬/훅 설정
- marimo 노트북
- GitHub Issue 템플릿

---

## 학습 목표

코스를 완료한 수강생은 다음을 할 수 있습니다:

1. **스캐폴딩 설계**: 데이터 분석 에이전트가 이해할 수 있는 레포지토리 구조를 설계하고, `AGENTS.md`에 레포 규칙과 워크플로 규약을 문서화할 수 있다.
2. **스킬/훅 구현**: Claude Code의 스킬과 훅을 정의하여 dbt 검증, marimo 리포트 생성, 비용 제어 등 분석 작업의 정책과 피드백 루프를 코드로 구현할 수 있다.
3. **오케스트레이션 구축**: GitHub Actions와 Claude Agent SDK를 사용하여 이슈 기반 7단계 자동 분석 워크플로를 처음부터 구축할 수 있다.
4. **완료 증거 설계**: 에이전트 작업의 완료를 기계적으로 검증할 수 있는 기준(dbt 테스트, 쿼리 검증, 리포트 아티팩트)을 설정할 수 있다.
5. **점진적 자율성 적용**: 작업 유형별로 자동화 수준을 분류하고, 에이전트에게 단계적으로 더 많은 자율성을 부여하는 전략을 수립할 수 있다.

---

## 모듈 구성

## 모듈 0: 환경 설정 및 프로젝트 이해

**총 학습 시간**: 35~48분

| 활동 | 내용 | 예상 시간 |
|------|------|-----------|
| 활동 1 | 스타터 레포 클론 및 로컬 환경 설정 | 5~8분 |
| 활동 2 | GCP 서비스 계정 및 GitHub Secret 설정 | 10~15분 |
| 활동 3 | Claude Agent SDK 인증 및 GitHub PAT 설정 | 5분 |
| 활동 4 | 합성 데이터 생성 및 BigQuery 적재 | 5~8분 |
| 활동 5 | dbt 모델 구조 탐색 | 5분 |
| 활동 6 | dbt 실행 및 검증 | 5~7분 |
| 활동 7 | Claude Code로 레포 이해도 기준선 측정 | 5분 |

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- `setup.sh`를 실행하여 Claude Code CLI, uv, dbt, marimo가 포함된 로컬 개발 환경을 **설정할 수 있다** — 네 도구 모두 버전 번호가 출력되는 것을 터미널에서 확인 *(검증: `claude --version && uv --version && dbt --version && marimo --version` 출력)*
- GCP 서비스 계정 JSON 키를 생성하고 `gh secret set` 명령으로 GitHub Secrets(`GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`)를 **구성할 수 있다** — `gh secret list` 실행 시 세 항목이 모두 표시됨 *(검증: `gh secret list` 출력)*
- `evidence/module-0-baseline.md` 파일을 직접 **작성할 수 있다** — Claude Code에게 레포 구조를 질문하고, 그 응답을 기준선(baseline) 문서로 기록 *(검증: `evidence/module-0-baseline.md` 파일 존재 및 내용)*
- `dbt run && dbt test`를 실행하여 6개 모델 전체 빌드 성공, 테스트 0 Fail 상태를 만들 수 있다 *(검증: 터미널 출력의 `Completed successfully` 메시지)*
- **하니스 설정(harness configuration)** 과 **파이프라인 산출물(pipeline output)** 의 차이를 예시와 함께 설명할 수 있다 — 이 코스 전체의 핵심 개념적 구분 *(검증: 활동 0-0 회고)*

#### 핵심 개념: 하니스 설정 vs 파이프라인 산출물

이 구분은 코스 전체를 관통하는 가장 중요한 개념입니다. 모듈 0에서 확립하고 이후 모든 모듈에서 참조합니다.

| 구분 | 정의 | 이 코스에서의 예시 |
|------|------|-----------------|
| **하니스 설정** (여러분이 엔지니어링하는 것) | 에이전트의 실행 환경을 구성하는 설정, 정책, 피드백 루프 | `.claude/settings.json`, 훅 스크립트, `AGENTS.md`, GitHub Actions 워크플로 YAML, Issue 템플릿 |
| **파이프라인 산출물** (하니스가 생산하는 것) | 에이전트가 하니스 안에서 실행하여 만들어 내는 데이터·리포트 | DAU/MAU 분석 차트, dbt mart 모델, marimo 리포트 HTML, `evidence/` 폴더의 검증 아티팩트 |

**왜 이 구분이 중요한가?**

수강생이 흔히 빠지는 함정: *"Claude Code가 dbt 모델을 잘 만들어주면 되지, 하니스가 왜 필요한가?"*

답: 에이전트가 단 한 번 올바른 결과를 내는 것은 쉽습니다. **일관되게, 안전하게, 검증 가능하게** 작업하도록 만드는 것이 하니스 엔지니어링입니다. 하니스 없는 에이전트는 매번 다른 방식으로 일하며, 비용을 초과하거나, 검증을 건너뛰거나, 파이프라인 산출물을 잘못 덮어씁니다.

> **모듈 0 관찰 과제**: 이번 모듈에서 여러분이 직접 *설정*하는 것(하니스)과 에이전트가 *실행하여 만드는* 것(산출물)을 항목별로 구분해 보세요. 활동 7 이후에 자신의 답을 점검합니다.

#### 배경

하니스 엔지니어링을 학습하기 전에, 에이전트가 작업할 환경을 먼저 준비해야 합니다. 스타터 레포에는 이미 완성된 dbt mart 모델(DAU/MAU 집계)이 포함되어 있습니다 — 이것은 **파이프라인 산출물의 예시**입니다. 수강생은 이 환경을 구성하면서 이후 모듈에서 스캐폴딩, 스킬/훅, 오케스트레이션을 구축할 **하니스 설정 기반**을 마련합니다.

모듈 0의 7개 활동은 두 가지 목적을 동시에 달성합니다:
1. **즉각적 목적**: Claude Code 에이전트가 실제로 작동하는 환경 구성
2. **교육적 목적**: 이후 모듈에서 하니스를 "추가"할 때 그 효과를 측정할 수 있는 기준선(baseline) 확립

#### 사전 준비

| 항목 | 설명 |
|------|------|
| Claude Code Pro 또는 Max 구독 | Claude Code CLI 사용에 필요 |
| GitHub 계정 | 레포 포크/클론 및 GitHub Actions 사용 |
| GCP 계정 | BigQuery 접근 (on-demand 가격) |
| macOS 또는 Linux 터미널 | CLI 명령어 실행 환경 |

### 활동

**활동 1: 스타터 레포 클론 및 로컬 환경 설정** *(예상 소요: 5~8분)*

스타터 레포를 클론하고 `setup.sh`를 실행합니다. 설치가 완료되면 각 도구의 버전을 확인합니다.

> 🔧 **하니스 vs 산출물**: `setup.sh`가 설치하는 Claude Code CLI, uv, dbt, marimo는 **하니스 인프라**입니다. 이 도구들 자체가 분석 결과를 만드는 것이 아니라, 나중에 에이전트가 분석을 수행할 때 사용하는 실행 환경입니다.

```bash
# 레포 클론
git clone <starter-repo-url> fittrack-analysis
cd fittrack-analysis

# 로컬 환경 자동 설정 (Claude Code, uv, dbt, marimo 설치)
./setup.sh

# 설치 검증 — 네 도구 모두 버전 출력 확인
claude --version   # 예: claude 1.x.x
uv --version       # 예: uv 0.x.x
dbt --version      # 예: dbt-core 1.x.x, dbt-bigquery
marimo --version   # 예: marimo 0.x.x
```

`setup.sh`가 설치하는 도구: **uv**(Python 패키지 관리자), **dbt**(dbt-bigquery 어댑터 포함), **marimo**(분석 노트북), **Claude Code CLI**(에이전트 인터페이스)

**활동 2: GCP 서비스 계정 및 GitHub Secret 설정** *(예상 소요: 10~15분)*

> 🔧 **하니스 vs 산출물**: GitHub Secrets(`GCP_SA_KEY`, `CLAUDE_TOKEN`)는 **하니스 설정**입니다. 에이전트가 BigQuery에 안전하게 접근할 수 있도록 허용하는 정책적 경계입니다. 나중에 에이전트가 생성하는 DAU 집계 데이터는 이 설정이 만드는 **산출물**입니다.

1. GCP 콘솔에서 서비스 계정 생성 — "BigQuery 데이터 편집자" 권한 부여 (뷰어 권한 불충분)
2. JSON 키 파일 다운로드
3. GitHub 레포 Settings > Secrets and variables > Actions에서 등록:
   - `GCP_SA_KEY`: 서비스 계정 JSON 키 내용 전체
   - `GCP_PROJECT_ID`: GCP 프로젝트 ID

```bash
# GitHub CLI를 사용한 Secret 등록 (파이프 방식으로 줄바꿈/따옴표 오류 방지)
gh secret set GCP_SA_KEY < key.json
gh secret set GCP_PROJECT_ID --body "<your-project-id>"
```

> 상세 절차: `instructor-setup-guide.md`의 "GCP 서비스 계정 설정" 섹션 참조

**활동 3: Claude Agent SDK 인증 및 GitHub PAT 설정** *(예상 소요: 5분)*

```bash
# 1. Claude Code 로그인 (브라우저 인증 진행)
claude login

# 2. 로그인 상태 확인
claude whoami

# 3. GitHub Secret에 토큰 등록
gh secret set CLAUDE_TOKEN --body "<YOUR_CLAUDE_TOKEN>"

# 4. 비대화형 모드 동작 테스트
claude -p "안녕하세요, 테스트입니다."
```

GitHub PAT(Personal Access Token) 또는 GitHub App을 추가로 생성하고 `GITHUB_PAT`(또는 `APP_ID` + `APP_PRIVATE_KEY`) Secret으로 등록합니다. 상세: `instructor-setup-guide.md` 참조.

**활동 3에서 등록하는 Secret 항목별 성격:**

| Secret 키 | 역할 | 분류 |
|-----------|------|------|
| `GCP_SA_KEY` | BigQuery 인증 | 하니스 설정 (접근 권한 경계) |
| `GCP_PROJECT_ID` | 프로젝트 식별 | 하니스 설정 (실행 컨텍스트) |
| `CLAUDE_TOKEN` | Claude Code 에이전트 인증 | 하니스 설정 (에이전트 신원) |
| `GITHUB_PAT` | GitHub API 접근 | 하니스 설정 (오케스트레이션 권한) |

**활동 4: 합성 데이터 생성 및 BigQuery 적재** *(예상 소요: 5~8분)*

> 🔧 **하니스 vs 산출물**: 합성 데이터(`raw_events`, `raw_users`, `raw_sessions`)는 **파이프라인의 입력 데이터**입니다. 하니스가 이 데이터를 어떻게 처리할지 정의하지만, 데이터 자체는 에이전트의 하니스 설정이 아닙니다.

> 💰 **BigQuery 비용**: `load_to_bigquery.py`는 `bq load` 명령을 사용한 적재로, on-demand 과금 구조에서는 **스토리지 비용만 발생**합니다(약 50만 건 ≈ 100MB → 월 ~$0.002). 쿼리 스캔 비용은 이후 `dbt run` 시 발생합니다.

```bash
# 합성 데이터 생성 (약 50만 건 이벤트, 1만 명 사용자)
python scripts/generate_synthetic_data.py

# BigQuery에 적재
python scripts/load_to_bigquery.py
```

| 테이블 | 레코드 수 (약) | 설명 |
|--------|--------------|------|
| `raw_events` | 50만 건 | 2026년 1분기 앱 이벤트 로그 |
| `raw_users` | 1만 명 | 사용자 프로필 |
| `raw_sessions` | 수십만 건 | 세션 단위 집계 |

**활동 5: dbt 모델 구조 탐색** *(예상 소요: 5분)*

> 🔧 **하니스 vs 산출물**: dbt 모델(`stg_*.sql`, `fct_*.sql`)은 이 코스에서 **파이프라인 산출물의 원천**입니다. 하지만 모듈 2에서 여러분이 정의할 dbt 검증 훅(hook)은 **하니스 설정**입니다. 구분 기준: "에이전트가 만드는가?" → 산출물. "에이전트의 행동을 제어하는 규칙인가?" → 하니스.

스타터 레포의 dbt 모델 레이어를 파악합니다:

```
models/
├── staging/
│   ├── stg_events.sql          -- 이벤트 클렌징, 타임존 통일
│   └── stg_users.sql           -- 사용자 프로필 정규화
├── marts/
│   ├── fct_daily_active_users.sql   -- DAU 집계 (그레인: 날짜 × 플랫폼)
│   ├── fct_monthly_active_users.sql -- MAU 집계 (그레인: 연월 × 플랫폼)
│   └── fct_retention_cohort.sql     -- 코호트 리텐션 (그레인: 코호트월 × 경과월)
└── schema.yml                  -- 모델 문서화 및 테스트 정의
```

각 모델의 역할 이해: `sources.yml`(원시 테이블 선언) → `staging/`(클렌징·타입 캐스팅) → `marts/`(비즈니스 로직 적용, 집계)

**활동 6: dbt 실행 및 검증** *(예상 소요: 5~7분)*

> 💰 **BigQuery 비용 추정**: `dbt run`은 staging + mart 모델 6개를 빌드합니다. 합성 데이터(~100MB)를 기준으로 전체 스캔 시 약 **0.6GB 처리 → $0.003** (on-demand $5/TB). 사실상 무료지만, 실습의 목적은 비용 추정 습관을 기르는 것입니다.

```bash
# dbt 의존성 설치 및 전체 모델 빌드 + 테스트 한 번에 실행
dbt deps && dbt run && dbt test

# BigQuery 콘솔에서 직접 확인
-- SELECT COUNT(*) FROM `<project>.<dataset>.stg_events`;
-- SELECT COUNT(*) FROM `<project>.<dataset>.fct_daily_active_users`;
```

**활동 7: Claude Code로 레포 이해도 기준선 측정** *(예상 소요: 5분)*

> 🔧 **이 활동의 위치**: 이것은 **하니스 효과 측정**입니다. 모듈 0에서는 아직 하니스(AGENTS.md, 훅)가 없습니다. 이 질문에 대한 에이전트의 현재 응답이 "하니스 없는 기준선"이 됩니다. 모듈 1에서 `AGENTS.md`를 추가한 후 같은 질문을 하면 하니스 효과를 체감할 수 있습니다.

모듈 1에서 `AGENTS.md` 추가 전후의 응답 품질 비교를 위해 현재 응답을 기록합니다:

```bash
# AGENTS.md 없는 상태에서의 응답 품질 측정
claude "이 dbt 프로젝트의 데이터 흐름을 설명해줘.
sources.yml의 소스 테이블에서 시작하여 staging 모델을 거쳐
mart 모델(fct_daily_active_users, fct_monthly_active_users)까지의
변환 과정을 단계별로 정리해줘. 각 모델의 그레인과 주요 컬럼도 포함해줘."
```

> **관찰 포인트**: 현 시점에는 하니스(`AGENTS.md`, `.claude/settings.json`, `.claude/commands/`)가 없으므로 에이전트가 파일 내용만으로 추측하여 답변합니다. 모듈 1에서 훅과 settings.json을, 모듈 2에서 슬래시 커맨드를 추가한 후 동일한 작업을 수행하여 하니스 효과를 비교하세요.

#### 핵심 개념 정리 — 도구별 모듈 역할

| 도구 | 모듈 0 | 모듈 1 | 모듈 2 | 모듈 3 | 모듈 4 |
|------|--------|--------|--------|--------|--------|
| `.claude/settings.json` | — | 훅·permissions 기초 | 커맨드에서 참조 | permissions.allow/deny 완성 | CI 환경 복제 |
| dbt | 환경 검증 | 훅으로 자동 컴파일 | 커맨드에서 run/test | 권한 내에서 실행 | 자동 실행 (파이프라인) |
| marimo | 버전 확인 | — | 리포트 커맨드 | — | 자동 생성 (stage:6~7) |
| Claude Code | 기준선 측정 | 훅/permissions 적용 | 커맨드 호출 | 권한 경계 테스트 | Agent SDK |
| GitHub Issues | — | — | 커맨드 #번호 입력 | — | 트리거 소스 (라벨 전환) |

#### 자기 점검 체크리스트

> **사용 방법**: 각 항목은 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다.
> - ✅ **합격**: "성공 기준"을 충족하면 체크박스에 표시하고 다음 항목으로 진행합니다.
> - ❌ **불합격**: "성공 기준"을 충족하지 못하면 "실패 시 조치"를 따라 문제를 해결한 뒤 재확인합니다.
> - **진행 조건**: 6개 항목 **모두 합격(✅)** 이어야 모듈 1로 진행할 수 있습니다.

##### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | 로컬 개발 환경 | 터미널에서 claude, uv, dbt, marimo 실행 가능 | 하니스 인프라 |
| 2 | BigQuery 합성 데이터 | `raw_events`(~50만 건), `raw_users`(~1만 명), `raw_sessions` 테이블 | 파이프라인 입력 |
| 3 | dbt 빌드·테스트 결과 | staging + mart 모델 6개 전체 빌드 성공, 테스트 0 Fail | 파이프라인 산출물 |
| 4 | GitHub Secrets | `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, 인증 토큰 | 하니스 설정 |
| 5 | Claude Code 기준선 응답 | 직접 기록 (텍스트) — `evidence/module-0-baseline.md` | 하니스 효과 측정용 |

### 자가 점검

**[점검 1/6] 도구 설치 확인**

- [ ] `claude --version` 실행 시 버전 번호가 출력되는가?
  - **검증 명령**: 터미널에서 `claude --version && uv --version && dbt --version && marimo --version` 실행
  - **✅ 합격 기준**: 네 도구 모두 버전 번호 출력 (예: `claude 1.x.x`, `uv 0.x.x`)
  - **❌ 불합격 시 조치**: `setup.sh` 로그에서 실패한 설치 단계 확인 → `npm install -g @anthropic-ai/claude-code` 수동 실행 후 재확인

**[점검 2/6] dbt 모델 빌드 확인**

- [ ] `dbt run` 실행 시 모든 모델(staging 3개 + mart 3개)이 성공적으로 빌드되는가?
  - **검증 명령**: `dbt run` 실행 후 출력 확인
  - **✅ 합격 기준**: `6 of 6 OK` 또는 `Completed successfully` 메시지, 에러 0건
  - **❌ 불합격 시 조치**: `dbt debug`로 BigQuery 연결 확인 → `profiles.yml`의 `project`, `dataset` 값 검증 → `GOOGLE_APPLICATION_CREDENTIALS` 환경변수 설정 확인

**[점검 3/6] BigQuery 데이터 적재 확인**

- [ ] BigQuery 콘솔에서 합성 데이터 테이블 조회가 가능한가?
  - **검증 명령**: BigQuery 콘솔 또는 `bq query 'SELECT COUNT(*) FROM <project>.<dataset>.stg_events'` 실행
  - **✅ 합격 기준**: 행 수가 약 500,000건 이상 (0보다 큰 값)
  - **❌ 불합격 시 조치**: `scripts/load_to_bigquery.py` 실행 로그에서 인증 오류 또는 프로젝트 ID 오류 확인 → `gcloud auth application-default login` 재실행

**[점검 4/6] GitHub Secrets 등록 확인**

- [ ] GitHub Secrets에 필수 항목이 모두 등록되어 있는가?
  - **검증 명령**: `gh secret list` 실행하여 Secret 이름 목록 확인
  - **✅ 합격 기준**: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, `GITHUB_PAT` (또는 `APP_ID`+`APP_PRIVATE_KEY`) 모두 목록에 표시
  - **❌ 불합격 시 조치**: GitHub UI > Settings > Secrets and variables > Actions에서 누락 항목 수동 등록 → `gh secret list`로 재확인

**[점검 5/6] dbt 테스트 통과 확인**

- [ ] `dbt test` 실행 시 모든 데이터 품질 테스트가 통과하는가?
  - **검증 명령**: `dbt test` 실행 후 출력 확인
  - **✅ 합격 기준**: 출력 마지막 줄에 `FAIL 0` 또는 `Passed` 메시지, `FAIL`로 표시된 테스트 없음
  - **❌ 불합격 시 조치**: 실패한 테스트명 확인 → `scripts/generate_synthetic_data.py` 재실행으로 데이터 품질 복구 → `dbt test` 재실행

**[점검 6/6] 핵심 개념 이해 확인**

- [ ] 모듈 0에서 수행한 활동 중 "하니스 설정(harness configuration)"에 해당하는 항목 3개, "파이프라인 산출물(pipeline output)"에 해당하는 항목 2개를 구분하여 나열할 수 있는가?
  - **검증 방법**: 아래 표를 직접 채운 뒤 정답 예시와 비교
  - **✅ 합격 기준**: 하니스 설정 3개 모두 정확히 분류, 산출물 2개 모두 정확히 분류 (정답 예시는 "핵심 개념: 하니스 설정 vs 파이프라인 산출물" 섹션 참조)

  | 분류 | 직접 작성할 항목 | 이유 |
  |------|----------------|------|
  | 하니스 설정 | _(직접 작성)_ | |
  | 하니스 설정 | _(직접 작성)_ | |
  | 하니스 설정 | _(직접 작성)_ | |
  | 파이프라인 산출물 | _(직접 작성)_ | |
  | 파이프라인 산출물 | _(직접 작성)_ | |

  <details>
  <summary>정답 예시 (작성 후에만 확인)</summary>

  | 분류 | 예시 항목 | 이유 |
  |------|---------|------|
  | 하니스 설정 | GitHub Secrets (`GCP_SA_KEY`, `CLAUDE_TOKEN`) | 에이전트의 접근 권한을 제어하는 정책 경계 |
  | 하니스 설정 | `setup.sh`가 설치하는 Claude Code CLI | 에이전트 실행 환경 자체 |
  | 하니스 설정 | `profiles.yml` (BigQuery 연결 설정) | 에이전트가 사용할 데이터 소스 설정 |
  | 파이프라인 산출물 | BigQuery의 `fct_daily_active_users` 테이블 | dbt가 변환하여 만든 분석용 집계 테이블 |
  | 파이프라인 산출물 | 합성 데이터 (`raw_events` 50만 건) | 에이전트가 분석할 원시 데이터 |

  </details>

  > **❌ 불합격 시 조치**: "핵심 개념: 하니스 설정 vs 파이프라인 산출물" 섹션으로 돌아가 정의를 다시 읽고, 각 활동의 🔧 아이콘 박스를 참조하세요.

> **모듈 진행 조건**: 위 6개 항목 **전부 ✅ 합격** 후 `modules/module-1.md`로 진행하세요.
> 상세 실습 가이드: `modules/module-0.md` 참조

---

## 모듈 1: 훅과 설정 엔지니어링 — settings.json으로 에이전트 정책 구현

**총 학습 시간**: 1.5~2시간

| 활동 | 내용 | 예상 시간 |
|------|------|-----------|
| 활동 1 | settings.json 구조 탐색 및 첫 번째 훅 등록 | 15~20분 |
| 활동 2 | PreToolUse 훅 — BigQuery 비용 가드 구현 및 테스트 | 25~30분 |
| 활동 3 | PostToolUse 훅 — dbt 모델 자동 컴파일 검증 구현 | 20~25분 |
| 활동 4 | permissions.allow / permissions.deny 정책 설정 | 15~20분 |
| 활동 5 | Stop 훅 — 작업 완료 요약 생성 구현 | 15~20분 |
| 활동 6 | 훅 의도적 실패 테스트 및 디버깅, 회고 | 15~20분 |

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- `.claude/settings.json`을 직접 작성하여 `PreToolUse`, `PostToolUse`, `Stop` 이벤트 훅을 등록하고, `cat .claude/settings.json | python -m json.tool` 실행 시 JSON 문법 오류가 없고 훅 항목이 출력되는 것을 확인할 수 있다 *(검증: 터미널 출력에 `"hooks"`, `"PreToolUse"`, `"PostToolUse"`, `"Stop"` 키가 모두 존재)*
- BigQuery 비용 가드 훅(`bq-cost-guard.sh`)을 구현하고, 1GB를 초과하는 쿼리를 dry-run으로 시뮬레이션했을 때 `❌ [bq-cost-guard] 비용 한도 초과!` 메시지와 함께 쿼리 실행이 차단되는 것을 터미널 출력으로 캡처할 수 있다 *(검증: `BQ_COST_LIMIT_BYTES=1` 환경변수로 임계값을 강제로 낮추어 차단 동작 확인)*
- `.claude/settings.json`의 `permissions.allow`와 `permissions.deny` 섹션을 설정하고, `git push --force` 및 `bq rm` 명령을 Claude Code 세션에서 실행했을 때 `Permission denied` 오류가 반환되는 것을 확인할 수 있다 *(검증: `claude "git push --force origin main 명령을 실행해줘"` 실행 후 거부 메시지 확인)*
- dbt 모델 파일을 편집한 직후 `PostToolUse` 훅이 `dbt compile`을 자동으로 실행하여 SQL 문법 오류를 즉시 감지하는 것을 시연할 수 있다 — 에이전트에게 의도적으로 잘못된 SQL을 작성하게 했을 때 훅이 오류를 보고하는 것을 확인 *(검증: 훅 실행 후 `dbt compile` 실패 메시지 또는 성공 메시지가 표시됨)*

#### 핵심 개념

**훅 (Hook) — 이벤트 기반 자동 정책 실행**

훅(hook)은 Claude Code가 특정 작업을 수행할 때 **자동으로 실행되는 셸 스크립트**입니다. 에이전트에게 규칙을 선언적으로 알려주는 `AGENTS.md`와 달리, 훅은 규칙 위반을 **기계적으로 차단하거나 자동으로 교정**합니다.

> **훅 (hook)**: 에이전트 실행 이벤트에 자동으로 반응하는 셸 스크립트 — 최초 사용 시 명확히 구분할 개념

| 훅 이벤트 | 트리거 시점 | 용도 예시 |
|-----------|------------|---------|
| `PreToolUse` | 도구(Bash, Edit, Write 등) 실행 **직전** | BigQuery 쿼리 비용 검사, 위험 명령 차단 |
| `PostToolUse` | 도구 실행 **직후** | dbt 컴파일 검증, marimo 문법 검사, 쿼리 로깅 |
| `Stop` | Claude Code 세션 **종료 시** | 작업 완료 요약 생성, 증거 파일 저장 |

**매처 (Matcher) — 어떤 도구·명령에 반응할지 지정**

매처(matcher)는 훅이 반응할 이벤트를 좁히는 패턴 문자열입니다. 매처를 너무 넓게 설정하면 false positive(정상 작업 차단)가, 너무 좁게 설정하면 누락이 발생합니다.

```json
// 매처 범위 비교 예시
{ "matcher": "Bash" }               // 모든 Bash 실행 — 너무 넓음
{ "matcher": "Bash(bq query*)" }    // bq query로 시작하는 명령만 — 적절
{ "matcher": "Edit(models/**/*.sql)" } // models/ 아래 SQL 파일 편집만 — 적절
```

**settings.json 구조 — 두 가지 핵심 섹션**

`.claude/settings.json`은 두 가지 하니스 설정을 담습니다:

```json
{
  "permissions": {
    "allow": ["Bash(dbt run:*)", "Bash(bq query --dry_run:*)", "Read", "Write", "Edit"],
    "deny":  ["Bash(git push --force:*)", "Bash(bq rm:*)", "Bash(DROP TABLE:*)"]
  },
  "hooks": {
    "PreToolUse": [{ "matcher": "Bash(bq query*)", "hooks": [{"type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh"}] }],
    "PostToolUse": [{ "matcher": "Edit(models/**/*.sql)", "hooks": [{"type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh"}] }],
    "Stop": [{ "hooks": [{"type": "command", "command": "bash .claude/hooks/stop-summary.sh"}] }]
  }
}
```

- **`permissions`**: Claude Code가 실행할 수 있는 명령의 허용/거부 목록 (정적 ACL)
- **`hooks`**: 이벤트 발생 시 동적으로 실행되는 스크립트 체인

**훅 스크립트 작성 규칙**

훅 스크립트는 표준 셸 스크립트(bash)입니다. 종료 코드로 Claude Code에게 결과를 전달합니다:
- **exit 0**: 작업 허용 / 훅 성공 — Claude Code가 계속 진행
- **exit 1**: 작업 차단 / 훅 실패 — Claude Code가 해당 작업을 중단하고 오류 메시지를 사용자에게 표시
- `PreToolUse` 훅에서 `exit 1` 반환 시 → 도구 실행 자체가 취소됨
- `PostToolUse` 훅에서 `exit 1` 반환 시 → 실행은 완료되었지만 오류 보고만

#### 사전 준비

모듈 1을 시작하기 전에 `AGENTS.md`가 존재해야 합니다. 모듈 0에서 생성하지 않았다면 먼저 작성하거나, 아래 최소 AGENTS.md로 시작할 수 있습니다:

```bash
# 최소 AGENTS.md 빠른 생성 (모듈 0 완료 후 이미 있다면 건너뜀)
cat > AGENTS.md << 'EOF'
# FitTrack 데이터 분석 에이전트 가이드

## BigQuery 정책
- 분석용 데이터셋: `fittrack_analytics` (읽기/쓰기 허용)
- 단일 쿼리 스캔 한도: 1GB 이하 (초과 시 dry-run 확인 후 진행)
- 프로덕션 데이터셋: `fittrack_production` (읽기 전용)

## dbt 모델 규약
- 분석 쿼리는 `models/marts/` 레이어(fct_*, dim_*)를 기반으로 작성
- 새 모델에는 `unique` + `not_null` 테스트 필수

## 금지 사항
- `git push --force` — 이력 손상 위험
- `bq rm`, `DROP TABLE`, `DELETE FROM` — 데이터 손실
- 스캔 1GB 초과 쿼리의 dry-run 없는 실행
EOF
```

### 활동

**활동 1: settings.json 구조 탐색 및 첫 번째 훅 등록** *(예상 소요: 15~20분)*

> 🔧 **하니스 설정**: `.claude/settings.json`과 그 안에 등록하는 훅 스크립트는 순수한 **하니스 설정**입니다. 에이전트가 실행하는 dbt 모델이나 BigQuery 쿼리 결과는 파이프라인 산출물이지만, 훅은 그 실행을 제어하는 정책 레이어입니다.

```bash
# .claude 디렉토리와 하위 구조 생성
mkdir -p .claude/hooks

# settings.json 스켈레톤 생성
cat > .claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {}
}
EOF

# JSON 문법 검증 (오류 없으면 포맷된 JSON 출력)
cat .claude/settings.json | python -m json.tool
```

가장 간단한 훅부터 등록합니다 — `Stop` 이벤트에 `echo` 명령을 실행하는 테스트 훅:

```bash
# Stop 훅 테스트 스크립트
cat > .claude/hooks/stop-summary.sh << 'EOF'
#!/usr/bin/env bash
# stop-summary.sh — 세션 종료 시 작업 요약 출력
# 역할: 하니스의 가시성(observability) 향상 — 에이전트가 무엇을 했는지 기록

# 현재 시각과 마지막 수정 파일 목록 출력
echo "=== 세션 완료 요약 ===" >&2
echo "종료 시각: $(date '+%Y-%m-%d %H:%M:%S')" >&2
echo "최근 수정 파일:" >&2
git diff --name-only HEAD 2>/dev/null | head -10 >&2 || echo "  (git 변경 없음)" >&2
exit 0
EOF
chmod +x .claude/hooks/stop-summary.sh
```

`settings.json`에 Stop 훅 등록:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
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

동작 확인:
```bash
# Claude Code 세션 시작 후 간단한 작업 후 종료 — Stop 훅 실행 확인
claude "현재 날짜를 알려줘"
# 종료 시 "=== 세션 완료 요약 ===" 메시지 출력 확인
```

**활동 2: PreToolUse 훅 — BigQuery 비용 가드 구현** *(예상 소요: 25~30분)*

> 💰 **비용 의식**: BigQuery on-demand 가격은 $5/TB입니다. 1GB 쿼리는 약 $0.005(0.5센트)로 소액이지만, 잘못 작성된 쿼리가 50GB를 스캔하면 $0.25가 됩니다. 에이전트가 반복적으로 실행할 수 있으므로 훅으로 자동 차단이 필수입니다.

`.claude/hooks/bq-cost-guard.sh` 생성:

```bash
cat > .claude/hooks/bq-cost-guard.sh << 'HOOKEOF'
#!/usr/bin/env bash
# bq-cost-guard.sh — BigQuery 쿼리 비용 가드
# 훅 타입: PreToolUse
# 매처: Bash (bq query 명령 감지)
# 역할: bq query 실행 전 dry-run으로 예상 스캔 바이트 확인 → 한도 초과 시 차단

set -euo pipefail

# 비용 한도 (기본값: 1GB, 환경변수로 조정 가능)
COST_LIMIT_BYTES="${BQ_COST_LIMIT_BYTES:-1073741824}"

# PreToolUse 훅 입력: STDIN으로 JSON 전달
# 형식: {"tool_name": "Bash", "tool_input": {"command": "..."}}
HOOK_INPUT=$(cat)
TOOL_INPUT=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# tool_input.command 키 확인
cmd = data.get('tool_input', {}).get('command', '') or data.get('command', '')
print(cmd)
" 2>/dev/null || echo "")

# bq query 명령이 아니면 통과 (다른 Bash 명령은 허용)
if [[ "$TOOL_INPUT" != *"bq query"* ]]; then
    exit 0
fi

# --dry_run 플래그가 이미 포함된 경우 통과 (dry-run 자체는 허용)
if [[ "$TOOL_INPUT" == *"--dry_run"* ]]; then
    exit 0
fi

# 쿼리 추출
QUERY=$(echo "$TOOL_INPUT" | sed "s/.*bq query[^'\"]*['\"]//;s/['\"].*//")

if [[ -z "$QUERY" ]]; then
    echo "⚠️  [bq-cost-guard] 쿼리 파싱 불가 — 수동으로 비용 확인하세요." >&2
    exit 0
fi

# dry-run으로 예상 스캔 바이트 확인
echo "🔍 [bq-cost-guard] dry-run 실행 중..." >&2
DRY_RUN_OUTPUT=$(bq query --dry_run --use_legacy_sql=false "$QUERY" 2>&1) || {
    echo "❌ [bq-cost-guard] dry-run 실패: $DRY_RUN_OUTPUT" >&2
    exit 1
}

# 스캔 바이트 추출
BYTES=$(echo "$DRY_RUN_OUTPUT" | python3 -c "
import json, sys, re
output = sys.stdin.read()
try:
    data = json.loads(output)
    print(data.get('statistics', {}).get('totalBytesProcessed', '0'))
except:
    match = re.search(r'totalBytesProcessed[\":\s]+([0-9]+)', output)
    print(match.group(1) if match else '0')
" 2>/dev/null || echo "0")

BYTES=${BYTES:-0}

# 사람이 읽기 쉬운 크기 표현
if [[ "$BYTES" -gt 1073741824 ]]; then
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1073741824:.2f} GB')")"
elif [[ "$BYTES" -gt 1048576 ]]; then
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1048576:.2f} MB')")"
else
    HUMAN_SIZE="$(python3 -c "print(f'{$BYTES/1024:.2f} KB')")"
fi

# 예상 비용 ($5/TB 기준)
COST_USD=$(python3 -c "print(f'\${$BYTES/1099511627776*5:.4f}')" 2>/dev/null || echo "\$0.0000")

echo "📊 [bq-cost-guard] 예상 스캔: $HUMAN_SIZE | 예상 비용: $COST_USD" >&2

# 한도 초과 시 차단 (exit 1)
if [[ "$BYTES" -gt "$COST_LIMIT_BYTES" ]]; then
    LIMIT_HUMAN="$(python3 -c "print(f'{$COST_LIMIT_BYTES/1073741824:.2f} GB')")"
    echo "❌ [bq-cost-guard] 비용 한도 초과! (한도: $LIMIT_HUMAN, 예상: $HUMAN_SIZE)" >&2
    echo "   최적화: WHERE 절 날짜 파티션 필터, mart 모델(fct_*) 활용" >&2
    exit 1  # Claude Code가 bq query 실행을 취소함
fi

echo "✅ [bq-cost-guard] 비용 한도 이내 — 쿼리 실행 허용" >&2
exit 0
HOOKEOF
chmod +x .claude/hooks/bq-cost-guard.sh
```

`settings.json`에 PreToolUse 훅 추가:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }
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

**훅 차단 동작 테스트** (성공 경로뿐만 아니라 차단 경로도 반드시 검증):

```bash
# 환경변수로 임계값을 1바이트로 낮춰 차단 동작 강제 테스트
# 실제 BigQuery 쿼리 없이도 차단 메시지가 출력되는지 확인
export BQ_COST_LIMIT_BYTES=1

echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' \
  | bash .claude/hooks/bq-cost-guard.sh

# 기대 출력: "❌ [bq-cost-guard] 비용 한도 초과!" 메시지와 exit 1
echo "훅 종료 코드: $?"  # 1이어야 함

# 테스트 후 원래 값 복원
unset BQ_COST_LIMIT_BYTES
```

> **BigQuery 실제 연결 없이 테스트**: dry-run 실행이 실패하면 훅이 exit 1을 반환합니다. 이 자체가 차단 동작의 검증입니다 (BigQuery 연결이 없으면 dry-run 실패 → 훅 차단).

**활동 3: PostToolUse 훅 — dbt 자동 컴파일 검증** *(예상 소요: 20~25분)*

dbt SQL 파일이 편집될 때마다 자동으로 `dbt compile`을 실행하여 SQL 문법 오류를 즉시 감지합니다:

```bash
cat > .claude/hooks/dbt-auto-test.sh << 'HOOKEOF'
#!/usr/bin/env bash
# dbt-auto-test.sh — dbt 모델 편집 후 자동 컴파일 검증
# 훅 타입: PostToolUse
# 매처: Write / Edit (models/**/*.sql 파일)
# 역할: dbt SQL 파일 수정 시 즉각 문법 오류 피드백 제공

set -uo pipefail

# PostToolUse 입력에서 수정된 파일 경로 추출
HOOK_INPUT=$(cat)
FILE_PATH=$(echo "$HOOK_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# tool_input.file_path 또는 path 키
path = data.get('tool_input', {}).get('file_path', '') or \
       data.get('tool_input', {}).get('path', '')
print(path)
" 2>/dev/null || echo "")

# dbt 모델 파일이 아니면 통과
if [[ "$FILE_PATH" != *"models/"*".sql" ]]; then
    exit 0
fi

echo "🔧 [dbt-auto-test] dbt 모델 변경 감지: $FILE_PATH" >&2
echo "   dbt compile 실행 중..." >&2

# dbt compile로 SQL 문법 검증 (빌드 없이 SQL 생성만 시도)
if dbt compile 2>&1 | tail -5 >&2; then
    echo "✅ [dbt-auto-test] dbt compile 성공 — SQL 문법 정상" >&2
    exit 0
else
    echo "❌ [dbt-auto-test] dbt compile 실패 — SQL 문법 오류 확인 필요" >&2
    exit 1  # Claude Code가 오류를 확인하도록 알림
fi
HOOKEOF
chmod +x .claude/hooks/dbt-auto-test.sh
```

`settings.json`에 PostToolUse 훅 추가:

```json
{
  "permissions": { "allow": [], "deny": [] },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }] }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }]
      },
      {
        "matcher": "Edit",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/dbt-auto-test.sh" }]
      }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "bash .claude/hooks/stop-summary.sh" }] }
    ]
  }
}
```

**의도적 실패 테스트**:

```bash
# 문법 오류가 있는 임시 dbt 모델 생성
echo "SELEC * FORM broken_table" > models/marts/test_broken.sql

# 에이전트가 이 파일을 편집했다고 가정하고 훅 직접 실행
echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/test_broken.sql"}}' \
  | bash .claude/hooks/dbt-auto-test.sh

# 기대 결과: "❌ [dbt-auto-test] dbt compile 실패" 메시지

# 테스트 파일 정리
rm models/marts/test_broken.sql
```

**활동 4: permissions.allow / permissions.deny 정책 설정** *(예상 소요: 15~20분)*

`permissions.allow`와 `permissions.deny`는 훅보다 먼저 평가되는 **정적 ACL(접근 제어 목록)**입니다. 훅은 동적 검증이지만, permissions는 패턴 매칭으로 즉시 허용/거부합니다.

```bash
# settings.json에 permissions 섹션 추가 (전체 파일)
cat > .claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(dbt source freshness:*)",
      "Bash(dbt ls:*)",
      "Bash(dbt deps:*)",
      "Bash(dbt debug:*)",
      "Bash(bq query --dry_run:*)",
      "Bash(bq show:*)",
      "Bash(bq ls:*)",
      "Bash(uv run:*)",
      "Bash(git diff:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout -b:*)",
      "Bash(git push:*)",
      "Bash(gh issue view:*)",
      "Bash(gh issue list:*)",
      "Bash(gh pr create:*)",
      "Bash(gh pr list:*)",
      "Bash(python3:*)",
      "Bash(jq:*)",
      "Read",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push origin main:*)",
      "Bash(git push origin master:*)",
      "Bash(bq rm:*)",
      "Bash(bq mk --force:*)",
      "Bash(dbt run --full-refresh:*)",
      "Bash(rm -rf:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh" }
        ]
      }
    ],
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
EOF

# JSON 문법 최종 검증
python -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 정상"
```

**permissions 규칙 해설**:

| 규칙 패턴 | 의미 | 분류 이유 |
|-----------|------|---------|
| `Bash(dbt run:*)` | `dbt run` 뒤 어떤 인수도 허용 | allow — dbt 실행은 분석의 핵심 |
| `Bash(bq query --dry_run:*)` | dry_run 플래그가 있는 bq query만 허용 | allow — dry-run은 안전 |
| `Bash(git push --force:*)` | force push 차단 | deny — 이력 손상 위험 |
| `Bash(bq rm:*)` | BigQuery 리소스 삭제 차단 | deny — 데이터 손실 |
| `Bash(dbt run --full-refresh:*)` | 전체 새로고침 차단 | deny — 대량 스캔 비용 위험 |

> **설계 원칙**: `deny`는 최소한으로 유지하고, 구체적인 패턴을 사용합니다. 너무 넓은 deny(`Bash(*)`)는 에이전트를 무력화합니다. 너무 좁은 allow(`Bash(dbt run --select fct_*:*)`)는 정당한 작업을 막습니다.

**활동 5: Stop 훅 — 작업 완료 요약 생성** *(예상 소요: 15~20분)*

Stop 훅을 업그레이드하여 분석 세션의 작업 요약을 `evidence/` 디렉토리에 저장합니다:

```bash
cat > .claude/hooks/stop-summary.sh << 'HOOKEOF'
#!/usr/bin/env bash
# stop-summary.sh — 세션 종료 시 작업 요약 생성
# 훅 타입: Stop
# 역할: 에이전트 세션의 가시성 확보 — 무엇이 변경되었는지 자동 기록

set -uo pipefail

# 증거 디렉토리 생성 (없으면)
mkdir -p evidence

# 현재 시각과 Git 변경 사항 수집
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
GIT_CHANGES=$(git diff --name-only HEAD 2>/dev/null | head -20 || echo "")
STAGED_CHANGES=$(git diff --cached --name-only 2>/dev/null | head -20 || echo "")

# JSON 형식으로 세션 요약 저장
python3 - << PYEOF
import json, os
from datetime import datetime

# 기존 로그 로드 (있으면)
log_file = "evidence/session_log.json"
sessions = []
if os.path.exists(log_file):
    try:
        with open(log_file) as f:
            sessions = json.load(f)
    except:
        sessions = []

# 새 세션 항목 추가
session = {
    "timestamp": "${TIMESTAMP}",
    "git_changes": """${GIT_CHANGES}""".strip().split('\n') if """${GIT_CHANGES}""".strip() else [],
    "staged_changes": """${STAGED_CHANGES}""".strip().split('\n') if """${STAGED_CHANGES}""".strip() else []
}
sessions.append(session)

# 최근 50개 세션만 유지
sessions = sessions[-50:]

with open(log_file, 'w') as f:
    json.dump(sessions, f, indent=2, ensure_ascii=False)

print(f"✅ [stop-summary] 세션 요약 저장: {log_file} ({len(sessions)}개 항목)")
PYEOF

exit 0
HOOKEOF
chmod +x .claude/hooks/stop-summary.sh
```

**활동 6: 훅 의도적 실패 테스트 및 디버깅** *(예상 소요: 15~20분)*

훅이 정상 동작하는지 확인하는 것만큼 **의도적으로 실패시키고 디버깅하는 것**이 중요합니다. 이것이 훅 엔지니어링의 핵심 역량입니다:

```bash
# 1. JSON 문법 오류 주입 테스트 — 오류가 있는 settings.json
echo '{"hooks": {"PreToolUse": [' > /tmp/bad_settings.json
python -m json.tool /tmp/bad_settings.json 2>&1 | head -3
# 기대: "Expecting value" 같은 JSON 파싱 오류 → settings.json은 항상 검증 후 저장

# 2. 훅 스크립트 실행 권한 누락 테스트
chmod -x .claude/hooks/bq-cost-guard.sh
# Claude Code 세션에서 bq query 실행 시 훅이 실행되지 않는 것 확인 (permission denied)
# 복구:
chmod +x .claude/hooks/bq-cost-guard.sh

# 3. 매처 너무 좁게 설정 시 → 정상 명령이 훅을 우회하는 것 확인
# "Bash(bq query --use_legacy_sql=false *)" 패턴은
# "bq query --nouse_legacy_sql ..." 명령은 감지하지 못함
# 교훈: 매처 패턴은 실제 에이전트가 생성하는 명령 형식에 맞게 테스트 필요

# 4. 전체 설정 최종 검증
echo "=== settings.json 검증 ===" && python -m json.tool .claude/settings.json && echo "✅ JSON 정상"
echo "=== 훅 스크립트 권한 확인 ===" && ls -la .claude/hooks/*.sh
```

#### Claude Code 프롬프트 예제

**settings.json 초안 생성**:

```bash
claude "AGENTS.md의 BigQuery 정책과 dbt 규약을 읽고
.claude/settings.json을 생성해줘.
permissions.allow: dbt run/test/compile/source freshness/ls/deps/debug,
bq query --dry_run, git status/log/diff/add/commit/checkout/push,
gh issue view/list, gh pr create/list, python3, jq, Read, Write, Edit
permissions.deny: git push --force, bq rm, dbt run --full-refresh, rm -rf
hooks:
- PreToolUse/Bash: bash .claude/hooks/bq-cost-guard.sh (비용 가드)
- PostToolUse/Write: bash .claude/hooks/dbt-auto-test.sh (dbt 컴파일 검증)
- PostToolUse/Edit: bash .claude/hooks/dbt-auto-test.sh
- Stop: bash .claude/hooks/stop-summary.sh (세션 요약)
생성 후 python -m json.tool로 JSON 문법 검증해줘."
```

**훅 스크립트 일괄 생성**:

```bash
claude "AGENTS.md의 BigQuery 비용 정책(1GB 한도, $5/TB)을 읽고
다음 3개 훅 스크립트를 생성해줘:
1. .claude/hooks/bq-cost-guard.sh
   - PreToolUse, Bash 매처
   - bq query 명령 감지 → dry-run 비용 확인 → BQ_COST_LIMIT_BYTES(기본 1GB) 초과 시 exit 1
   - 예상 스캔량, 비용, 판정 메시지 stderr 출력
2. .claude/hooks/dbt-auto-test.sh
   - PostToolUse, Write/Edit 매처
   - models/**/*.sql 파일 변경 시 dbt compile 실행 → 실패 시 exit 1
3. .claude/hooks/stop-summary.sh
   - Stop 이벤트
   - git diff --name-only로 변경 파일 목록 → evidence/session_log.json 저장
각 스크립트 생성 후 chmod +x 실행, JSON 주석(# 설명)으로 훅 타입과 역할 명시."
```

#### 관찰-수정-창작 사이클

**관찰(observe)**

훅 설정 전후로 동일한 에이전트 작업을 실행하여 차이를 관찰합니다:

```bash
# 훅 없는 상태 (훅 등록 전 또는 임시 비활성화 상태)에서 실행:
# 에이전트가 비용이 큰 쿼리를 실행하면 아무 경고 없이 진행됨

# 훅 등록 후 실행:
# - bq query 실행 시 비용 가드 훅 작동
# - dbt SQL 파일 편집 시 자동 컴파일 검증
# - 세션 종료 시 작업 요약 생성
```

**회고 질문**

아래 질문에 대한 답변을 `evidence/module-1-retrospective.md`에 기록하세요.

**영역 A: 훅 동작 검증**

1. **비용 가드 차단 테스트 결과**: `BQ_COST_LIMIT_BYTES=1`로 설정하여 강제 차단을 테스트했을 때 어떤 메시지가 출력되었는가? 실제 BigQuery 연결 없이도 차단 동작을 검증하는 방법은 무엇인가?

2. **의도적 실패 케이스**: 훅 스크립트를 의도적으로 실패시키는 방법을 3가지 나열하라 (예: 실행 권한 제거, JSON 문법 오류, 훅 경로 오탈자). 각각을 어떻게 디버깅하는가?

**영역 B: 정책 설계 판단**

3. **매처 범위 트레이드오프**: `PreToolUse` 훅의 매처를 `"Bash"` (모든 Bash)로 설정했을 때 vs `"Bash(bq query*)"` (bq query만)로 설정했을 때, 각각의 false positive와 false negative는 어떤 것이 있는가?

4. **permissions vs hooks 선택 기준**: `git push --force`를 차단할 때 `permissions.deny`를 사용하는 것이 더 나은가, 아니면 `PreToolUse` 훅으로 구현하는 것이 더 나은가? 두 접근법의 차이점을 설명하라.

**영역 C: 하니스 정합성**

5. **AGENTS.md와 settings.json 정합성**: `AGENTS.md`에 "BigQuery 스캔 1GB 한도"를 명시했다면, `bq-cost-guard.sh`의 `BQ_COST_LIMIT_BYTES` 기본값도 `1073741824` (1GB)이어야 합니다. 이 수치가 일치하는지 확인하고, 단일 소스(예: `.claude/thresholds.env`)에서 관리하는 구조를 설계하라.

**하니스 생성**

회고 결과를 바탕으로:

1. **매처 패턴 조정**: false positive가 발생한 훅의 매처 패턴을 좁혀 수정합니다
2. **임계값 환경 파일 생성**: `.claude/thresholds.env`에 `BQ_COST_LIMIT_BYTES=1073741824` 정의 후 훅 스크립트에서 `source .claude/thresholds.env`로 로드하는 구조로 리팩토링
3. **JSON 스키마 검증 자동화**: `python -m json.tool .claude/settings.json`을 pre-commit 훅에 포함하여 settings.json 수정 시 JSON 문법 자동 검증

#### 자기 점검 체크리스트

> **사용 방법**: 각 항목을 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다. 6개 항목 **모두 합격**이어야 모듈 2로 진행합니다.

##### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | `.claude/settings.json` | 레포 루트 기준 `.claude/` 하위 — JSON 문법 정상, hooks + permissions 섹션 포함 | 하니스 설정 |
| 2 | `bq-cost-guard.sh` | `.claude/hooks/` — 실행 권한 부여, PreToolUse + Bash 매처 | 하니스 설정 |
| 3 | `dbt-auto-test.sh` | `.claude/hooks/` — 실행 권한 부여, PostToolUse + Write/Edit 매처 | 하니스 설정 |
| 4 | `stop-summary.sh` | `.claude/hooks/` — 실행 권한 부여, Stop 이벤트 | 하니스 설정 |
| 5 | `evidence/session_log.json` | Stop 훅 실행 후 자동 생성 | 파이프라인 산출물 |
| 6 | 회고 기록 | `evidence/module-1-retrospective.md` — 차단 테스트 결과 + 매처 트레이드오프 분석 | 하니스 효과 측정 |

### 자가 점검

**[점검 1/6] settings.json 존재 및 JSON 문법 정상**

- [ ] `.claude/settings.json`이 존재하고 JSON 문법 오류가 없는가?
  - **검증 명령**: `cat .claude/settings.json | python -m json.tool`
  - **✅ 합격 기준**: 포맷된 JSON이 오류 없이 출력됨 (`"hooks"`, `"permissions"` 키 모두 존재)
  - **❌ 불합격 시 조치**: `python -m json.tool` 오류 메시지의 줄 번호를 확인하여 JSON 문법 오류 수정 (주로 trailing comma, 빠진 따옴표)

**[점검 2/6] 훅 스크립트 실행 권한 확인**

- [ ] 3개 훅 스크립트가 모두 실행 권한을 가지고 있는가?
  - **검증 명령**: `ls -la .claude/hooks/*.sh`
  - **✅ 합격 기준**: 파일 권한이 `-rwxr-xr-x` (실행 비트 `x` 설정됨) 3개 파일 모두
  - **❌ 불합격 시 조치**: `chmod +x .claude/hooks/*.sh` 실행

**[점검 3/6] 비용 가드 훅 차단 동작**

- [ ] `BQ_COST_LIMIT_BYTES=1`로 설정 시 bq-cost-guard.sh가 exit 1을 반환하는가?
  - **검증 명령**: `export BQ_COST_LIMIT_BYTES=1; echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' | bash .claude/hooks/bq-cost-guard.sh; echo "exit: $?"; unset BQ_COST_LIMIT_BYTES`
  - **✅ 합격 기준**: `❌ [bq-cost-guard]` 메시지 출력 및 exit code가 `1`
  - **❌ 불합격 시 조치**: 훅 스크립트의 `COST_LIMIT_BYTES` 비교 로직(`[[ "$BYTES" -gt "$COST_LIMIT_BYTES" ]]`) 확인

**[점검 4/6] PostToolUse 훅 dbt 오류 감지**

- [ ] 잘못된 SQL이 포함된 파일을 models/에 저장했을 때 dbt-auto-test.sh가 exit 1을 반환하는가?
  - **검증 명령**: `echo "SELEC * FORM broken" > models/marts/test_broken.sql; echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/test_broken.sql"}}' | bash .claude/hooks/dbt-auto-test.sh; echo "exit: $?"; rm models/marts/test_broken.sql`
  - **✅ 합격 기준**: `❌ [dbt-auto-test] dbt compile 실패` 메시지 출력 및 exit code가 `1`
  - **❌ 불합격 시 조치**: `dbt compile` 명령이 실행 가능한지 확인(`dbt compile` 직접 실행), 훅 내부의 파일 경로 패턴(`*models/*\.sql`) 검토

**[점검 5/6] permissions.deny 차단 설정**

- [ ] `permissions.deny`에 `git push --force`, `bq rm`, `dbt run --full-refresh`, `rm -rf`가 포함되어 있는가?
  - **검증 명령**: `python -m json.tool .claude/settings.json | grep -A 10 '"deny"'`
  - **✅ 합격 기준**: deny 배열에 4개 패턴이 모두 존재
  - **❌ 불합격 시 조치**: `settings.json`의 `permissions.deny` 배열에 누락된 패턴 추가 후 JSON 재검증

**[점검 6/6] 핵심 개념 이해 — 훅 vs permissions**

- [ ] `permissions.deny`와 `PreToolUse 훅`의 차이를 설명하고, 각각을 언제 사용할지 결정할 수 있는가?
  - **검증 방법**: `evidence/module-1-retrospective.md`의 "영역 B 질문 4번" 답변을 확인
  - **✅ 합격 기준**: "permissions.deny는 패턴 매칭으로 즉시 거부 (동적 검사 불가), 훅은 실행 시점에 값/상태를 검사 가능 (동적 비용 계산 등)"의 요지가 포함됨
  - **❌ 불합격 시 조치**: 핵심 개념 섹션의 "permissions vs hooks" 표를 다시 읽고, `bq-cost-guard.sh`가 왜 deny 패턴으로 대체될 수 없는지 생각해보세요 (dry-run 비용 계산은 실행 시점에만 가능)

> **모듈 진행 조건**: 위 6개 항목 **전부 ✅ 합격** 후 모듈 2로 진행하세요.
> 상세 실습 가이드: `modules/module-1.md` 참조

---

## 모듈 2: 슬래시 커맨드 작성 — 에이전트 작업 명세화

**총 학습 시간**: 1.5~2시간

| 활동 | 내용 | 예상 시간 |
|------|------|-----------|
| 활동 1 | .claude/commands/ 구조 파악 및 첫 번째 커맨드 작성 | 15~20분 |
| 활동 2 | /analyze 커맨드 — 분석 요청 → 노트북 생성 전 과정 명세화 | 25~30분 |
| 활동 3 | /check-cost 커맨드 — BigQuery dry-run 비용 조회 | 15~20분 |
| 활동 4 | /validate-models 및 /generate-report 커맨드 작성 | 20~25분 |
| 활동 5 | $ARGUMENTS 변수 활용 — 동적 커맨드 설계 | 10~15분 |
| 활동 6 | 커맨드 체인 실습 및 완료 증거 설계, 회고 | 15~20분 |

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- `.claude/commands/analyze.md`를 작성하고, `claude "/analyze 2026년 1월 DAU 추이 분석 기간: 2026-01-01 ~ 2026-01-31"` 실행 후 `analyses/` 디렉토리에 `.py` marimo 노트북 파일이 생성되는 것을 `ls analyses/*.py`로 확인할 수 있다 *(검증: 파일명이 `analysis_dau_*.py` 형식을 따르며 내용에 BigQuery 쿼리와 marimo 셀 구조가 포함됨)*
- `$ARGUMENTS` 변수를 활용하는 동적 슬래시 커맨드를 작성하고, 동일한 커맨드로 `기간: 2026-01`, `기간: 2026-02`를 입력했을 때 서로 다른 이름의 분석 파일이 생성되는 것을 시연할 수 있다 *(검증: `ls analyses/` 출력에 `analysis_dau_202601.py`와 `analysis_dau_202602.py` 두 파일이 존재)*
- `/check-cost` 커맨드를 실행하여 SQL 쿼리의 BigQuery 예상 비용이 `✅ 안전 범위` / `⚠️ 주의 (1~10GB)` / `❌ 위험 (10GB 초과)` 판정과 함께 MB/GB 수치로 출력되는 것을 터미널에서 캡처할 수 있다 *(검증: 출력에 스캔량 수치와 $USD 추산 및 판정 메시지 포함)*
- `/analyze` → `/validate-models` → `/generate-report` 커맨드를 순서대로 실행하여 `evidence/` 디렉토리에 `dbt_test_results.json`, `query_cost_log.json`, `report_manifest.json` 3개 파일이 생성되고 `cat evidence/dbt_test_results.json | python -m json.tool`로 필수 필드가 모두 채워진 것을 확인할 수 있다 *(검증: `total_tests`, `passed`, `failed` 필드 존재)*

#### 핵심 개념

**슬래시 커맨드 (Slash Command) — 명시적 작업 호출**

슬래시 커맨드(slash command)는 `.claude/commands/` 디렉토리의 마크다운 파일로 정의되는, 사용자가 `/명령어`로 명시적으로 호출하는 작업 명세서입니다.

> **슬래시 커맨드**: `.claude/commands/` 아래 `.md` 파일로 정의된 재사용 가능한 에이전트 작업 단위 — 최초 사용 시 명확히 구분할 개념

| 구분 | 슬래시 커맨드 (slash command) | 훅 (hook) |
|------|-------------------------------|-----------|
| 트리거 | 사람이 `/명령어`로 명시 호출 | 이벤트 발생 시 자동 실행 |
| 파일 위치 | `.claude/commands/*.md` | `.claude/settings.json` + 스크립트 |
| 목적 | 올바른 작업 방법을 제공 | 잘못된 작업을 차단/교정 |
| 예시 | `/analyze`: 분석 흐름 전체 | `PreToolUse`: 비용 가드 |

**커맨드 파일 구조 — 마크다운 명세**

커맨드 파일은 Claude Code가 `/` 명령어를 받았을 때 그 내용을 프롬프트로 사용합니다. 좋은 커맨드 파일은 다음 섹션을 포함합니다:

```markdown
# /커맨드명 — 한 줄 목적 요약

한 단락 설명: 이 커맨드가 무엇을 하는지, 언제 사용하는지.

## 입력

- `$ARGUMENTS`: 입력 형식 설명 (예: "GitHub Issue 번호 또는 분석 요청 텍스트")
- 선택 입력이 있으면 명시

## 실행 단계

### 1단계: [단계 이름]
구체적인 지시 사항...

### 2단계: [단계 이름]
...

## 출력

완료 후 다음 형식으로 보고:
[출력 형식 예시]

## 제약 조건

- 반드시 지켜야 할 규칙
- 금지 사항
```

**$ARGUMENTS — 동적 커맨드 입력**

`$ARGUMENTS`는 커맨드 실행 시 `/커맨드명 [입력 텍스트]`에서 `[입력 텍스트]` 부분이 대입되는 변수입니다:

```bash
# 사용 예
claude "/analyze 2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"
# → analyze.md 파일에서 $ARGUMENTS = "2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"
```

**완료 증거 (Proof of Completion) — 텍스트 보고를 대체하는 JSON 아티팩트**

에이전트의 "완료했습니다" 텍스트 보고 대신, 기계적으로 검증 가능한 JSON 파일을 증거로 사용합니다:

| 증거 파일 | 내용 | 핵심 검증 필드 |
|-----------|------|---------------|
| `evidence/dbt_test_results.json` | dbt 테스트 전체 결과 | `timestamp`, `total_tests`, `passed`, `failed` |
| `evidence/query_cost_log.json` | 실행 쿼리의 스캔 바이트 및 비용 | `estimated_bytes`, `within_threshold`, `cost_usd` |
| `evidence/report_manifest.json` | 생성된 리포트 파일 목록 | `notebook_source`, `outputs[].format`, `outputs[].path` |

#### 사전 준비

모듈 2는 모듈 1(훅과 설정 엔지니어링)을 완료한 후 시작합니다. 다음이 준비되어 있어야 합니다:

```
✅ .claude/settings.json   — 훅 등록 완료 (모듈 1 산출물)
✅ .claude/hooks/          — bq-cost-guard.sh, dbt-auto-test.sh, stop-summary.sh
✅ AGENTS.md               — BigQuery 정책, dbt 규약 포함
✅ analyses/, evidence/, reports/ 디렉토리 존재
```

`.claude/commands/` 디렉토리는 **아직 없는 상태**입니다 — 이것이 모듈 2의 핵심 산출물입니다.

### 활동

**활동 1: .claude/commands/ 구조 파악 및 첫 번째 커맨드 작성** *(예상 소요: 15~20분)*

> 🔧 **하니스 설정**: `.claude/commands/` 디렉토리의 모든 `.md` 파일은 **하니스 설정**입니다. 에이전트가 이 커맨드를 사용하여 생성하는 marimo 노트북, dbt 모델, JSON 증거는 **파이프라인 산출물**입니다.

```bash
# .claude/commands 디렉토리 생성
mkdir -p .claude/commands

# 가장 단순한 커맨드부터 시작 — /hello
cat > .claude/commands/hello.md << 'EOF'
# /hello — 커맨드 구조 연습

이 커맨드는 커맨드 파일 구조를 이해하기 위한 예제입니다.

## 입력

- `$ARGUMENTS`: 인사 대상 이름 (예: `/hello FitTrack팀`)

## 실행 단계

### 1단계: 인사말 출력
현재 시각과 `$ARGUMENTS`에 입력된 이름을 포함한 인사말을 출력합니다.

### 2단계: 프로젝트 상태 요약
`AGENTS.md`를 읽고 프로젝트명과 주요 구성 요소(BigQuery, dbt, marimo)를 한 줄로 요약합니다.

## 출력

```
안녕하세요, [이름]! [현재 시각]
프로젝트: FitTrack 데이터 분석 — BigQuery + dbt + marimo 기반
```

## 제약 조건

- 외부 API 호출 금지
- 파일 생성/수정 없이 읽기 작업만 수행
EOF

# 테스트
claude "/hello 데이터팀"
```

> **관찰 포인트**: `/hello 데이터팀` 실행 시 `$ARGUMENTS`가 "데이터팀"으로 대체되어 출력되는지 확인합니다. 커맨드 파일이 에이전트의 프롬프트 역할을 하는 것을 직접 체험하는 것이 이 활동의 목적입니다.

**활동 2: /analyze 커맨드 — 분석 요청 → 노트북 생성 전 과정 명세화** *(예상 소요: 25~30분)*

> 💰 **BigQuery 비용 내장**: `/analyze` 커맨드는 쿼리 실행 전 dry-run 비용 확인 단계를 반드시 포함합니다. 새 쿼리 추가 시 예상 비용을 미리 출력하는 것이 on-demand 가격 환경에서의 필수 습관입니다. 합성 데이터(~100MB) 기준 DAU 쿼리 1회 실행 약 $0.0003.

```bash
cat > .claude/commands/analyze.md << 'EOF'
# /analyze — 분석 요청 → end-to-end 데이터 분석 실행

GitHub Issue 또는 분석 요청 텍스트를 받아 dbt 모델 확인 → 쿼리 설계 →
marimo 노트북 생성 → 완료 증거 저장까지 전 과정을 수행합니다.

## 입력

- `$ARGUMENTS`: 다음 중 하나
  - GitHub Issue 번호: `#42` 형식
  - 분석 요청 텍스트: `"[지표] [기간] [세그먼트(선택)]"` 형식
    - 예: `"2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"`

## 실행 단계

### 1단계: 분석 요청 파싱
- GitHub Issue 번호인 경우: `gh issue view $ISSUE_NUMBER` 실행하여 본문 확인
- 텍스트인 경우: 직접 파싱
- 추출 항목: 지표, 기간(시작일~종료일), 세그먼트, 기대 산출물

### 2단계: 기존 dbt 모델 탐색
`models/` 디렉토리에서 사용 가능한 mart 모델 확인:
- `fct_daily_active_users` — DAU 일별 집계
- `fct_monthly_active_users` — MAU 월별 집계
- `fct_retention_cohort` — 코호트 리텐션
기존 모델로 분석 가능하면 재사용, 불가능할 경우만 신규 모델 작성.

### 3단계: 비용 사전 검증 (필수)
새 쿼리가 필요한 경우 반드시 dry-run으로 비용 확인:
```bash
bq query --dry_run --use_legacy_sql=false "[SQL]"
```
예상 스캔량과 비용($5/TB 기준)을 출력합니다.
1GB 초과 시 쿼리 최적화(파티션 필터, SELECT * 제거, mart 재사용) 후 재확인.

### 4단계: dbt 모델 작성 (필요 시만)
기존 mart로 충분하지 않은 경우에만:
- `models/marts/` 하위에 `fct_` 또는 `dim_` 접두사로 파일 생성
- `schema.yml`에 `unique` + `not_null` 테스트 추가
- `dbt run --select [모델명]`으로 빌드 확인

### 5단계: marimo 노트북 생성
파일 경로: `analyses/analysis_[지표]_[YYYYMM].py`
구조 (순서대로):
1. 분석 제목·기간·핵심 발견 요약 (`mo.md` 셀)
2. BigQuery 연결 및 데이터 로드
3. 데이터 변환·집계 계산
4. 시각화 (plotly 또는 altair)
5. 결론 및 제안 (`mo.md` 셀)

### 6단계: 완료 증거 저장
`evidence/query_cost_log.json`에 실행된 쿼리의 비용 정보 기록:
```json
{
  "timestamp": "[ISO 8601]",
  "analysis_topic": "[분석 주제]",
  "queries": [
    {
      "sql_preview": "[SQL 앞 100자]",
      "estimated_bytes": 0,
      "cost_usd": 0.0,
      "within_threshold": true
    }
  ]
}
```

## marimo 노트북 작성 규약

- 차트 제목·축 레이블·범례: **한국어**
- 숫자: 천 단위 쉼표, 비율은 소수점 2자리 (%)
- BigQuery 연결: `google.cloud.bigquery.Client(project=os.environ["BQ_PROJECT_ID"])`
- 변수명·함수명: 영어, 주석: 한국어

## 출력

분석 완료 후:
```
## 분석 완료

### 생성된 파일
- 📓 analyses/analysis_[주제]_[기간].py
- 📦 models/marts/fct_[이름].sql (신규 모델이 있을 경우)

### BigQuery 비용
- 예상 스캔량: X.X GB
- 예상 비용: $X.XXXX USD (on-demand $5/TB 기준)

### dbt 테스트
- ✅ N개 통과 / ❌ N개 실패
```

## 제약 조건

- **금지**: 쿼리 비용 사전 확인 없이 bq query 실행
- **금지**: `staging/` 레이어 직접 쿼리 (mart 모델 기반으로 작성)
- **금지**: 기존 marimo 노트북 파일 덮어쓰기 (새 파일명 생성)
- **필수**: `analyses/` 경로로 노트북 저장
- **필수**: 완료 증거 JSON 저장 (`evidence/query_cost_log.json`)
EOF
```

테스트:

```bash
# 커맨드 실행 — 실제 BigQuery 연결이 있으면 분석 수행, 없으면 커맨드 구조 확인
claude "/analyze 2026년 1월 DAU 추이 기간: 2026-01-01~2026-01-31 세그먼트: platform"

# 노트북 파일 생성 확인
ls analyses/*.py
```

**활동 3: /check-cost 커맨드 작성** *(예상 소요: 15~20분)*

`/check-cost`는 분석 작업 시작 전 BigQuery 쿼리 비용을 빠르게 확인하는 유틸리티 커맨드입니다:

```bash
cat > .claude/commands/check-cost.md << 'EOF'
# /check-cost — BigQuery 쿼리 비용 사전 확인

SQL 쿼리를 입력받아 BigQuery dry-run으로 예상 스캔량과 비용을 조회합니다.
실제 쿼리 실행 전에 비용을 확인하는 습관을 위한 커맨드입니다.

## 입력

- `$ARGUMENTS`: 비용을 확인할 SQL 쿼리 텍스트
  - 예: `SELECT COUNT(*) FROM \`project.dataset.fct_daily_active_users\``

## 실행 단계

### 1단계: dry-run 실행
```bash
bq query --dry_run --use_legacy_sql=false "$ARGUMENTS"
```

### 2단계: 비용 계산 및 판정
스캔 바이트 수를 가져와 다음 기준으로 판정:
- **✅ 안전 범위**: 1GB 미만 — 예상 비용 $0.005 미만
- **⚠️ 주의 (1~10GB)**: 최적화 검토 권장 — 예상 비용 $0.005~$0.05
- **❌ 위험 (10GB 초과)**: 실행 전 반드시 재검토 필요 — 예상 비용 $0.05 이상

### 3단계: 최적화 제안 (주의/위험 판정 시)
비용이 높을 경우:
1. WHERE 절에 날짜 파티션 필터(`_PARTITIONDATE`) 추가
2. `SELECT *` 대신 필요한 컬럼만 명시
3. mart 모델(`fct_*`) 사용으로 사전 집계 데이터 활용

## 출력

```
## BigQuery 비용 확인

**SQL 미리보기**: [SQL 앞 100자]...
**예상 스캔량**: X.XX GB (X bytes)
**예상 비용**: $X.XXXX USD (on-demand $5/TB 기준)
**판정**: ✅ 안전 범위 | ⚠️ 주의 | ❌ 위험

[주의/위험 판정 시] **최적화 제안**: ...
```

## 제약 조건

- `--dry_run` 없이 실제 쿼리를 실행하지 않음 (비용 발생 방지)
- 결과를 `evidence/query_cost_log.json`에 추가 기록
EOF
```

테스트:

```bash
# 간단한 쿼리로 비용 확인 테스트
claude "/check-cost SELECT COUNT(*) FROM \`<project>.fittrack_analytics.fct_daily_active_users\`"
# 기대 출력: 예상 스캔량, 비용, ✅/⚠️/❌ 판정
```

**활동 4: /validate-models 및 /generate-report 커맨드 작성** *(예상 소요: 20~25분)*

```bash
# /validate-models — dbt 모델 빌드 및 테스트 실행
cat > .claude/commands/validate-models.md << 'EOF'
# /validate-models — dbt 모델 빌드·테스트 및 결과 보고

`dbt run` → `dbt test` 순서로 실행하고 결과를 요약하여 증거 파일에 저장합니다.

## 입력

- `$ARGUMENTS`: 선택적. 특정 모델 이름 지정 시 해당 모델만 실행
  - 예: `/validate-models fct_daily_active_users` — 특정 모델만
  - 빈 경우: 전체 모델 실행

## 실행 단계

### 1단계: dbt 의존성 확인
`dbt deps`를 실행하여 패키지가 설치되어 있는지 확인합니다.

### 2단계: dbt run
`$ARGUMENTS`가 있으면 `dbt run --select $ARGUMENTS`, 없으면 `dbt run` 실행.

### 3단계: dbt test
`dbt test` 실행. 실패한 테스트의 이름과 모델을 수집합니다.

### 4단계: 결과 저장
`evidence/dbt_test_results.json`에 저장:
```json
{
  "timestamp": "[ISO 8601]",
  "run_scope": "전체 | 특정 모델명",
  "total_tests": 0,
  "passed": 0,
  "failed": 0,
  "failed_tests": []
}
```

## 출력

```
## dbt 검증 결과

**실행 범위**: 전체 / [모델명]
**빌드**: ✅ N개 성공 / ❌ N개 실패
**테스트**: ✅ N개 통과 / ❌ N개 실패

[실패한 테스트가 있을 경우]
**실패 상세**:
- [테스트명]: [모델명] — [실패 원인]
```

## 제약 조건

- dbt 실패 시 중단하지 않고 전체 결과를 수집 후 보고
- 증거 파일 저장은 성공/실패 무관하게 반드시 수행
EOF

# /generate-report — marimo 노트북 → HTML/PDF 내보내기
cat > .claude/commands/generate-report.md << 'EOF'
# /generate-report — marimo 노트북을 HTML/PDF 리포트로 내보내기

marimo 노트북을 실행하여 HTML과 PDF 형식으로 내보내고 결과를 기록합니다.

## 입력

- `$ARGUMENTS`: marimo 노트북 파일 경로
  - 예: `/generate-report analyses/analysis_dau_202601.py`

## 실행 단계

### 1단계: 노트북 존재 확인
`$ARGUMENTS` 경로에 파일이 존재하는지 확인합니다.

### 2단계: HTML 내보내기
```bash
uv run marimo export html $ARGUMENTS -o reports/$(basename $ARGUMENTS .py).html
```
예상 비용: $0 (BigQuery 미사용)

### 3단계: 리포트 매니페스트 저장
`evidence/report_manifest.json`에 저장:
```json
{
  "timestamp": "[ISO 8601]",
  "notebook_source": "[노트북 파일 경로]",
  "outputs": [
    { "format": "html", "path": "reports/[파일명].html", "size_bytes": 0 }
  ]
}
```

## 출력

```
## 리포트 생성 완료

**소스**: [노트북 경로]
**생성 파일**:
- 📄 reports/[파일명].html (X KB)

**확인 방법**: 브라우저에서 HTML 파일 열기
```

## 제약 조건

- `reports/` 디렉토리가 없으면 자동 생성
- 같은 이름의 리포트 파일이 존재하면 타임스탬프를 파일명에 추가하여 덮어쓰기 방지
EOF
```

**활동 5: $ARGUMENTS 변수 활용 — 동적 커맨드 설계** *(예상 소요: 10~15분)*

`$ARGUMENTS`를 더 구조화된 방식으로 파싱하도록 커맨드를 개선합니다:

```bash
# analyze.md에 구조화된 입력 파싱 추가
# 다음 형식을 지원:
# /analyze 지표: DAU 기간: 2026-01~2026-03 세그먼트: platform
# /analyze #42
# /analyze 2026년 Q1 DAU 추이

# 테스트: 동일한 커맨드로 다른 기간 분석
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31"
# → analyses/analysis_dau_202601.py 생성 확인

claude "/analyze 2026년 2월 DAU 기간: 2026-02-01~2026-02-28"
# → analyses/analysis_dau_202602.py 생성 확인 (202601과 다른 파일)

ls analyses/
# 기대 출력: analysis_dau_202601.py, analysis_dau_202602.py
```

> **$ARGUMENTS 활용 원칙**:
> - 구조화 입력(`키: 값` 형식)이 자유 형식 텍스트보다 에이전트의 파싱 일관성이 높습니다
> - 커맨드 파일의 `## 입력` 섹션에서 예시 형식을 명확하게 제시하면 에이전트가 정확하게 파싱합니다
> - `$ARGUMENTS`가 비어있을 경우의 기본값 동작을 `## 제약 조건`에 명시하세요

**활동 6: 커맨드 체인 실습 및 완료 증거 설계** *(예상 소요: 15~20분)*

슬래시 커맨드를 순서대로 실행하는 분석 체인을 수행합니다:

```bash
# 전체 분석 체인 — 순서가 중요
# 1. 비용 확인 (선택적 but 권장)
claude "/check-cost SELECT date, COUNT(DISTINCT user_id) as dau FROM \`<project>.fittrack_analytics.fct_daily_active_users\` WHERE date BETWEEN '2026-01-01' AND '2026-01-31' GROUP BY 1 ORDER BY 1"

# 2. 분석 실행
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31 세그먼트: platform"

# 3. dbt 모델 검증
claude "/validate-models"

# 4. 리포트 생성
claude "/generate-report analyses/analysis_dau_202601.py"

# 5. 최종 산출물 확인
tree analyses/ evidence/ reports/
cat evidence/dbt_test_results.json | python -m json.tool
```

> **커맨드 체인 설계 원칙**: 각 커맨드는 독립적으로 실행 가능해야 합니다. `/generate-report`가 `/analyze` 결과에 의존한다면 `## 사전 조건` 섹션에 명시하여 에이전트가 순서를 인지하게 합니다.

#### Claude Code 프롬프트 예제

**커맨드 파일 일괄 생성**:

```bash
claude "AGENTS.md를 읽고 FitTrack 프로젝트용 4개 슬래시 커맨드를 생성해줘.
.claude/commands/ 아래에 analyze.md, validate-models.md, generate-report.md, check-cost.md를 생성해줘.
각 파일에 ## 입력, ## 실행 단계, ## 출력, ## 제약 조건 섹션 포함.
analyze.md: 분석 요청 파싱 → 기존 mart 모델 탐색 → 비용 dry-run 확인 → 신규 dbt 모델(필요 시) → marimo 노트북(analyses/ 경로) → 완료 증거 JSON 저장(evidence/).
check-cost.md: $ARGUMENTS SQL dry-run → 스캔량·비용·판정(✅안전 / ⚠️주의 / ❌위험).
validate-models.md: dbt run → dbt test → evidence/dbt_test_results.json 저장.
generate-report.md: marimo export html → reports/ 저장 → evidence/report_manifest.json 저장.
BigQuery on-demand 비용 기준: $5/TB. 한도: 1GB."
```

**커맨드 프롬프트 개선 요청**:

```bash
claude "/analyze를 실행해보니 파일명이 analyses/analysis_202601.py로 생성됐어.
AGENTS.md의 marimo 규약에 따르면 파일명은 analysis_[지표]_[기간].py 형식이어야 해.
analyze.md의 실행 단계 5단계에서 파일명 생성 로직을 더 구체적으로 명시해줘:
지표는 $ARGUMENTS에서 추출한 주제(영문, 소문자, 언더스코어)를 사용하고,
기간은 YYYYMM 형식으로 시작일의 연월을 사용해줘."
```

#### 관찰-수정-창작 사이클

**관찰(observe)**

커맨드 작성 전후로 동일한 분석 요청의 결과를 비교합니다:

```bash
# 커맨드 없이 자유 형식 프롬프트
claude "2026년 1월 DAU 추이를 분석하고 marimo 노트북으로 만들어줘"
# 결과: 파일명, 노트북 구조, 증거 파일 생성 여부가 매번 달라질 수 있음

# 커맨드 사용 후
claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31 세그먼트: platform"
# 결과: analyze.md에 명세된 단계가 일관되게 실행됨
```

**회고 질문**

아래 질문에 대한 답변을 `evidence/module-2-retrospective.md`에 기록하세요.

**영역 A: 커맨드 명세 품질**

1. **추측 발생 분석**: `/analyze` 커맨드 실행 시 에이전트가 명세하지 않은 사항을 추측한 경우가 있었는가? (예: 파일명 형식, 차트 종류, 데이터 필터링 기준) 추측을 없애려면 커맨드의 어느 섹션에 어떤 내용을 추가해야 하는가?

2. **커맨드 경계 설계**: `/analyze` 커맨드가 너무 많은 책임(비용 확인 + 모델 작성 + 노트북 생성 + 증거 저장)을 가지고 있지는 않은가? 이를 더 작은 커맨드로 분리하면 어떤 장단점이 있는가?

**영역 B: $ARGUMENTS 활용**

3. **파싱 일관성**: `$ARGUMENTS`에 자유 형식 텍스트를 입력했을 때 에이전트가 기간, 세그먼트 등을 항상 올바르게 파싱했는가? 파싱 실패를 줄이기 위해 `## 입력` 섹션에 어떤 예시와 형식을 추가할 수 있는가?

4. **기본값 처리**: `$ARGUMENTS`가 비어있거나 형식이 잘못된 경우 에이전트가 어떻게 행동했는가? 커맨드 파일에 기본값 처리 로직을 명시하면 더 나은 결과를 얻을 수 있는가?

**영역 C: 커맨드-훅 연계**

5. **훅 보완 역할**: 모듈 1에서 설정한 `bq-cost-guard.sh` PreToolUse 훅과 `/check-cost` 커맨드가 비용 관련 작업을 어떻게 나누어 담당하는가? 둘 다 필요한 이유는 무엇인가? (힌트: 사전 명시적 확인 vs 자동 차단)

6. **완료 증거의 충분성**: `evidence/dbt_test_results.json`, `query_cost_log.json`, `report_manifest.json` 3개 파일로 "분석이 올바르게 완료되었다"는 것을 기계적으로 검증할 수 있는가? 검증할 수 없는 항목은 무엇인가? (예: DAU ≤ MAU 검증)

**하니스 생성**

회고 결과를 바탕으로:

1. **커맨드 명세 개선**: 추측이 발생한 단계에 더 구체적인 지시와 예시를 추가합니다
2. **$ARGUMENTS 파싱 강화**: 입력 형식 예시를 `## 입력` 섹션에 최소 2개 추가합니다
3. **완료 증거 확장**: 의미론적 검증(`evidence/metric_sanity_check.json` — `dau <= mau`) 항목을 `/validate-models` 커맨드에 추가합니다
4. **커맨드 README 작성**: `.claude/commands/README.md`에 4개 커맨드의 역할과 실행 순서를 정리합니다

#### 자기 점검 체크리스트

> **사용 방법**: 각 항목을 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다. 6개 항목 **모두 합격**이어야 모듈 3으로 진행합니다.

##### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | 커맨드 파일 4개 | `.claude/commands/analyze.md`, `check-cost.md`, `validate-models.md`, `generate-report.md` | 하니스 설정 |
| 2 | marimo 분석 노트북 | `analyses/analysis_dau_202601.py` (또는 동일 구조 파일) | 파이프라인 산출물 |
| 3 | dbt 검증 증거 | `evidence/dbt_test_results.json` — `total_tests`, `passed`, `failed` 필드 | 파이프라인 산출물 |
| 4 | 비용 로그 증거 | `evidence/query_cost_log.json` — `estimated_bytes`, `within_threshold` 필드 | 파이프라인 산출물 |
| 5 | 리포트 매니페스트 | `evidence/report_manifest.json` — `outputs[].format`, `outputs[].path` 필드 | 파이프라인 산출물 |
| 6 | 회고 기록 | `evidence/module-2-retrospective.md` — 추측 발생 분석 + 커맨드-훅 연계 설명 | 하니스 효과 측정 |

### 자가 점검

**[점검 1/6] 커맨드 파일 4개 존재 및 구조 확인**

- [ ] `.claude/commands/`에 4개 커맨드 파일이 존재하고 각 파일에 `## 입력`, `## 실행 단계`, `## 출력`, `## 제약 조건` 섹션이 모두 있는가?
  - **검증 명령**: `ls .claude/commands/*.md` (파일 목록 확인) + `grep -l "## 제약 조건" .claude/commands/*.md` (섹션 존재 확인)
  - **✅ 합격 기준**: 4개 파일 모두 존재, 각 파일에 4개 섹션 헤더가 포함됨
  - **❌ 불합격 시 조치**: 누락된 파일 생성, 또는 Claude Code에게 "analyze.md에 ## 제약 조건 섹션을 추가해줘" 요청

**[점검 2/6] /analyze 실행 후 노트북 생성**

- [ ] `/analyze` 커맨드 실행 후 `analyses/` 디렉토리에 `.py` marimo 파일이 생성되는가?
  - **검증 명령**: `claude "/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31"` 실행 후 `ls analyses/*.py`
  - **✅ 합격 기준**: `analyses/` 디렉토리에 `.py` 파일 1개 이상 생성, 파일명에 `analysis_` 접두사 포함
  - **❌ 불합격 시 조치**: `analyze.md`의 5단계 파일 경로 지시(`analyses/analysis_[지표]_[기간].py`)가 명확한지 확인

**[점검 3/6] /check-cost 비용 판정 출력**

- [ ] `/check-cost` 실행 시 스캔량(MB/GB), 예상 비용($USD), 안전/주의/위험 판정이 모두 출력되는가?
  - **검증 명령**: `claude "/check-cost SELECT COUNT(*) FROM \`<project>.fittrack_analytics.fct_daily_active_users\`"` 실행
  - **✅ 합격 기준**: 출력에 스캔량 수치, `$X.XXXX` 형식 비용, `✅`/`⚠️`/`❌` 판정 중 하나가 포함됨
  - **❌ 불합격 시 조치**: `check-cost.md`의 2단계 판정 기준(1GB/10GB 임계값)이 명확하게 명시되어 있는지 확인, BigQuery 연결 설정 확인

**[점검 4/6] /validate-models 완료 증거 파일 생성**

- [ ] `/validate-models` 실행 후 `evidence/dbt_test_results.json`에 필수 필드가 있는가?
  - **검증 명령**: `claude "/validate-models"` 실행 후 `cat evidence/dbt_test_results.json | python -m json.tool`
  - **✅ 합격 기준**: 파일이 존재하고 `total_tests`, `passed`, `failed` 키가 모두 포함됨
  - **❌ 불합격 시 조치**: `validate-models.md`의 4단계 JSON 스키마를 확인하여 누락된 필드가 명세에 포함되어 있는지 확인

**[점검 5/6] $ARGUMENTS 동적 입력 — 기간별 다른 파일 생성**

- [ ] 동일한 `/analyze` 커맨드에 다른 기간을 입력했을 때 서로 다른 파일명의 노트북이 생성되는가?
  - **검증 명령**: `/analyze 2026년 1월 DAU 기간: 2026-01-01~2026-01-31` 실행 후 `/analyze 2026년 2월 DAU 기간: 2026-02-01~2026-02-28` 실행, `ls analyses/` 확인
  - **✅ 합격 기준**: `analyses/` 디렉토리에 `202601`과 `202602`가 각각 포함된 파일 2개 존재
  - **❌ 불합격 시 조치**: `analyze.md`의 5단계에서 `$ARGUMENTS`의 기간 파싱과 파일명 생성 로직을 더 구체적으로 명시

**[점검 6/6] 슬래시 커맨드와 훅의 역할 구분 이해**

- [ ] `bq-cost-guard.sh` 훅(모듈 1)과 `/check-cost` 커맨드(모듈 2)가 각각 어떤 시나리오를 커버하는지 설명할 수 있는가?
  - **검증 방법**: `evidence/module-2-retrospective.md`의 영역 C 질문 5번 답변을 확인
  - **✅ 합격 기준**: 훅(자동·수동 모두 차단, 사용자가 명시 안 해도 작동)과 커맨드(사용자가 명시적으로 비용을 확인하고 싶을 때 사용)의 역할 차이가 서술됨
  - **❌ 불합격 시 조치**: 모듈 1의 "훅 vs 슬래시 커맨드" 개념 표를 다시 읽고, `bq-cost-guard.sh`이 없다면 어떤 상황에서 비용이 초과될 수 있는지 생각해보세요

> **모듈 진행 조건**: 위 6개 항목 **전부 ✅ 합격** 후 모듈 3으로 진행하세요.
> 상세 실습 가이드: `modules/module-2.md` 참조

---

## 모듈 3: 권한 오케스트레이션 — Claude Code 권한 정책으로 에이전트 경계 설계

**총 학습 시간**: 1.5~2시간

| 활동 | 내용 | 예상 시간 |
|------|------|-----------|
| 활동 1 | Claude Code 권한 모델 구조 탐색 및 설정 파일 계층 이해 | 15~20분 |
| 활동 2 | 데이터 분석 에이전트를 위한 허용 규칙(allow) 설계 및 구현 | 20~25분 |
| 활동 3 | 위험 작업 차단을 위한 거부 규칙(deny) 구현 및 동작 검증 | 20~25분 |
| 활동 4 | GitHub Actions `permissions:` 키 설계 — CI 환경 권한 분리 | 15~20분 |
| 활동 5 | 로컬 vs CI 다중 환경 권한 정책 설계 | 15~20분 |
| 활동 6 | 권한 경계 종합 테스트 및 회고 | 10~15분 |

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- `.claude/settings.json`의 `permissions.allow`와 `permissions.deny` 섹션이 각각 3개 이상의 규칙을 포함하도록 직접 작성하고, `cat .claude/settings.json | python -m json.tool` 실행 시 JSON 문법 오류 없이 두 섹션이 출력되는 것을 확인할 수 있다 *(검증: 터미널 출력에 `"permissions"`, `"allow"`, `"deny"` 키가 모두 존재)*
- `claude "git push --force origin main을 실행해줘"` 명령을 실행했을 때 에이전트가 `Permission denied` 또는 거부 메시지를 출력하며 실행을 거부하는 것을 터미널 출력으로 캡처할 수 있다 *(검증: 터미널 출력에 거부 메시지 또는 `not allowed` 포함 확인)*
- GitHub Actions 워크플로 YAML(`.github/workflows/auto-analyze.yml`)에서 `permissions: issues: write` 와 `contents: write` 키를 직접 가리키며, 각 권한이 7단계 파이프라인의 어느 단계에서 어떤 이유로 필요한지 설명할 수 있다 *(검증: YAML 파일에서 해당 키 존재 확인, 설명 문서는 `evidence/module-3-permissions-rationale.md`에 기록)*
- 로컬 개발 환경(`.claude/settings.json`)과 CI 환경(GitHub Actions `permissions:` 키)의 권한 설계가 의도적으로 다르게 설계되어 있으며, 그 이유를 "로컬 개발자 맥락 vs 자동화 파이프라인 맥락"의 차이로 설명하는 문서를 작성할 수 있다 *(검증: `evidence/module-3-permissions-rationale.md`의 "로컬 vs CI 권한 비교" 섹션 존재)*

#### 핵심 개념

**권한 오케스트레이션(Permissions Orchestration)이란?**

> **권한 오케스트레이션 (permissions orchestration)**: 에이전트가 작업 맥락(로컬 개발 / CI 파이프라인 / 다중 에이전트 협업)에 따라 서로 다른 권한 경계를 갖도록 정책을 설계하고 조정하는 행위 — 최초 사용 시 명확히 구분할 개념

모듈 1에서 `permissions.allow`와 `permissions.deny`의 기초를 배웠다면, 모듈 3에서는 **권한이 전체 하니스 오케스트레이션과 어떻게 상호작용하는가**를 배웁니다. 핵심 질문은 다음과 같습니다:

- 로컬에서 Claude Code를 대화형으로 사용할 때와, GitHub Actions에서 자동으로 실행될 때 에이전트에게 동일한 권한을 줘도 되는가?
- 단계별 파이프라인에서 각 에이전트 단계에 필요한 권한은 어떻게 최소화(principle of least privilege)할 수 있는가?
- GitHub Actions의 `permissions:` 키와 Claude Code의 `permissions.allow/deny`는 서로 어떻게 연관되는가?

**Claude Code 권한 계층 구조**

Claude Code 권한은 세 가지 범위(scope)에서 적용되며, 더 구체적인 범위가 우선합니다:

```
글로벌 설정 (~/.claude/settings.json)
  └─ 모든 Claude Code 세션에 적용되는 기본 권한
  
프로젝트 설정 (.claude/settings.json)  ← 이 코스에서 주로 작성
  └─ 해당 레포지토리에서 Claude Code 실행 시 적용
  └─ 글로벌 설정보다 구체적이므로 우선 적용
  
로컬 설정 (.claude/settings.local.json)
  └─ 개별 개발자의 로컬 환경에만 적용 (gitignore 권장)
  └─ 팀 공유 규칙이 아닌 개인 설정에 사용
```

> 🔧 **하니스 vs 산출물**: 이 세 파일 모두 **하니스 설정**입니다. `.claude/settings.json`을 팀 레포에 커밋하면 팀 전체가 동일한 권한 경계 하에서 에이전트를 사용합니다.

**`permissions.allow`와 `permissions.deny`의 역할 분담**

```json
{
  "permissions": {
    "allow": [
      "Bash(bq:*)",
      "Bash(dbt:*)",
      "Bash(marimo:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push origin HEAD:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(bq rm:*)",
      "Bash(bq update:*)",
      "Bash(gcloud projects delete:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

| 구분 | 역할 | 설계 원칙 |
|------|------|-----------|
| `allow` (허용 목록) | 에이전트가 실행 가능한 명령의 **화이트리스트** | 데이터 분석 작업에 필요한 최소 권한만 포함 |
| `deny` (거부 목록) | 에이전트가 절대 실행할 수 없는 명령의 **블랙리스트** | 되돌리기 어려운(irreversible) 작업을 명시적으로 차단 |
| 우선순위 | `deny` > `allow` | deny 목록에 있으면 allow에 있어도 차단 |

**GitHub Actions `permissions:` 키 — CI 환경 권한 분리**

Claude Code의 `permissions.allow/deny`가 **에이전트 도구 사용 권한**을 제어한다면, GitHub Actions의 `permissions:` 키는 **워크플로가 GitHub API에 접근할 수 있는 권한**을 제어합니다. 두 권한 체계는 서로 독립적이지만, 함께 전체 파이프라인의 보안 경계를 구성합니다.

```yaml
# .github/workflows/auto-analyze.yml 의 권한 설정 예시
jobs:
  orchestrate:
    permissions:
      issues: write      # 이슈 코멘트 작성, 라벨 부착/제거에 필요
      contents: write    # PR 생성, 파일 커밋에 필요
      pull-requests: write  # PR 본문 수정, 라벨 부착에 필요
```

| GitHub Actions `permissions:` 키 | 필요한 이유 |
|----------------------------------|------------|
| `issues: write` | 각 단계 완료 후 이슈 코멘트 작성, 라벨 전환 |
| `contents: write` | 분석 결과 파일 커밋, 브랜치 푸시 |
| `pull-requests: write` | 자동 PR 생성 및 설명 작성 |
| `actions: read` | 워크플로 실행 상태 읽기 (선택적) |

> **최소 권한 원칙**: GitHub Actions의 `permissions:`는 필요한 권한만 명시적으로 열어주는 방식으로 설계해야 합니다. 기본값이 레포 전체 쓰기 권한이므로, 명시적으로 `write` 또는 `read`로 제한하는 것이 보안상 좋습니다.

**로컬 개발 환경 vs CI 환경 권한 비교**

| 항목 | 로컬 개발 (`.claude/settings.json`) | CI 환경 (GitHub Actions) |
|------|-------------------------------------|--------------------------|
| 사용 맥락 | 개발자가 대화형으로 사용 | 자동화 파이프라인에서 비대화형 실행 |
| 권한 주체 | 개별 개발자 Claude Code 세션 | GitHub Actions Runner + Claude Agent SDK |
| 위험 수준 | 개발자가 즉시 오류 확인 가능 | 오류 시 자동 확산 위험, 더 엄격한 제한 필요 |
| `git push` | `git push origin HEAD:*` 허용 | `contents: write` 권한으로 워크플로가 제어 |
| 비용 제한 | `BQ_COST_LIMIT_BYTES` 환경변수 | 동일한 훅 스크립트가 CI에서도 실행됨 |

> 🔧 **핵심 설계 판단**: CI 환경에서는 사람이 실시간으로 감독하지 않으므로, 로컬보다 **더 엄격한** 권한 경계가 필요합니다. 예를 들어, 로컬에서는 `git push origin HEAD:*`를 허용하지만 CI에서는 워크플로가 PR 브랜치에만 푸시하도록 제한합니다.

### 활동

**활동 1: Claude Code 권한 모델 구조 탐색 및 설정 파일 계층 이해** *(예상 소요: 15~20분)*

> 🔧 **하니스 vs 산출물**: 권한 설정(`.claude/settings.json`)은 **하니스 설정**입니다. 이것이 에이전트가 생성하는 DAU 분석 차트(산출물)를 만들어내는 것이 아니라, 에이전트가 어떤 방식으로 일할 수 있는지를 결정하는 경계입니다.

현재 레포의 Claude Code 설정 파일 현황을 파악합니다:

```bash
# 전역 설정 파일 확인 (모든 세션에 적용)
cat ~/.claude/settings.json 2>/dev/null || echo "전역 설정 없음"

# 프로젝트 설정 파일 확인 (이 레포에만 적용)
cat .claude/settings.json 2>/dev/null || echo "프로젝트 설정 없음"

# 로컬 개발자 설정 파일 확인 (gitignore 권장)
cat .claude/settings.local.json 2>/dev/null || echo "로컬 설정 없음"

# 현재 settings.json의 permissions 섹션 확인 (모듈 1에서 생성)
python -m json.tool .claude/settings.json | grep -A 20 '"permissions"'
```

**모듈 1에서 설정한 권한 현황 점검**: 이미 `permissions.allow`와 `permissions.deny`가 있다면 어떤 규칙이 있는지 확인합니다. 없다면 이 모듈에서 처음 설계합니다.

**활동 2: 데이터 분석 에이전트를 위한 허용 규칙(allow) 설계 및 구현** *(예상 소요: 20~25분)*

> 💰 **BigQuery 비용 관련 권한**: `Bash(bq:*)` 허용 규칙은 모든 BigQuery CLI 명령을 허용합니다. 비용 제어를 위해 훅(`bq-cost-guard.sh`)과 함께 사용해야 합니다. 권한 설정만으로는 비용을 제어할 수 없습니다 — 훅이 실제 비용 가드를 담당합니다.

FitTrack 데이터 분석 에이전트에게 필요한 최소 권한을 설계합니다:

```json
{
  "permissions": {
    "allow": [
      "Bash(bq:*)",
      "Bash(bq query:*)",
      "Bash(dbt run:*)",
      "Bash(dbt test:*)",
      "Bash(dbt compile:*)",
      "Bash(marimo run:*)",
      "Bash(marimo export:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push origin HEAD:*)",
      "Bash(gh issue comment:*)",
      "Bash(gh issue edit --add-label:*)",
      "Bash(gh issue edit --remove-label:*)",
      "Bash(gh pr create:*)"
    ]
  }
}
```

허용 규칙 설계 원칙:
- **작업 범위 명시**: `bq:*`보다 `bq query:*`가 더 안전하지만, 유연성을 위해 `bq:*` 허용 후 `deny`로 위험 명령 차단
- **git 작업 분리**: `git push`는 허용하되, `git push --force`는 deny 목록에서 차단
- **GitHub CLI**: 이슈 관리 및 PR 생성에 필요한 `gh` 명령만 허용

다음 Claude Code 프롬프트로 권한 설계를 에이전트에게 요청합니다:

```bash
claude "현재 .claude/settings.json을 분석하고, FitTrack 데이터 분석 에이전트가
필요한 최소 권한을 permissions.allow 섹션에 추가해줘.

필요한 작업 유형:
1. BigQuery 쿼리 실행 (bq query)
2. dbt 모델 실행/테스트/컴파일 (dbt run, dbt test, dbt compile)
3. marimo 노트북 실행 및 HTML/PDF 내보내기
4. Git 작업 (add, commit, push)
5. GitHub CLI로 이슈 코멘트, 라벨 관리, PR 생성

각 규칙에 왜 이 권한이 필요한지 JSON 주석(// 형식)으로 설명하고,
최소 권한 원칙(principle of least privilege)을 적용해줘.

수정 후 python -m json.tool .claude/settings.json으로 문법 검증해줘."
```

**활동 3: 위험 작업 차단을 위한 거부 규칙(deny) 구현 및 동작 검증** *(예상 소요: 20~25분)*

되돌리기 어려운(irreversible) 작업을 차단하는 거부 규칙을 구현하고, 실제로 차단되는지 검증합니다:

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push --force-with-lease:*)",
      "Bash(git reset --hard:*)",
      "Bash(bq rm:*)",
      "Bash(bq update --schema:*)",
      "Bash(gcloud projects delete:*)",
      "Bash(gcloud iam service-accounts delete:*)",
      "Bash(rm -rf:*)",
      "Bash(gh repo delete:*)"
    ]
  }
}
```

**거부 규칙 동작 검증**:

```bash
# deny 설정 후 검증 — git push --force 차단 확인
claude "git push --force origin main 명령을 실행해줘"
# 기대 출력: Permission denied 또는 해당 명령이 허용되지 않는다는 메시지

# bq rm 차단 확인
claude "bq rm fittrack_raw.raw_events 테이블을 삭제해줘"
# 기대 출력: 거부 메시지 (테이블을 실제로 삭제하려 하면 안 됨)
```

> **관찰 포인트**: 에이전트가 거부 메시지를 받았을 때 어떻게 반응하는지 관찰하세요. 좋은 에이전트는 "이 명령이 차단되었으므로 대안을 제시합니다"와 같이 응답하고, 나쁜 에이전트는 무한 루프에 빠지거나 우회를 시도합니다. 우회를 시도한다면 deny 규칙을 더 강화해야 합니다.

**활동 4: GitHub Actions `permissions:` 키 설계** *(예상 소요: 15~20분)*

GitHub Actions 워크플로 YAML에서 CI 환경의 권한을 설계합니다:

```yaml
# .github/workflows/auto-analyze.yml 권한 섹션 (개념도)
name: Auto Analyze

on:
  issues:
    types: [labeled]

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    # GitHub API 접근 권한 — 최소 권한 원칙 적용
    permissions:
      issues: write        # 이슈 코멘트 작성 + 라벨 부착/제거
      contents: write      # 파일 커밋 + 브랜치 푸시
      pull-requests: write # PR 생성 + 설명 작성

    steps:
      # ... (상세 단계는 모듈 4에서 구현)
```

**권한 설계 문서 작성** (`evidence/module-3-permissions-rationale.md`):

```markdown
# 권한 설계 근거 (module-3)

## Claude Code permissions.allow/deny — 로컬 개발 환경

### 허용 규칙 (allow) 근거
| 규칙 | 필요한 이유 |
|------|------------|
| `Bash(bq:*)` | BigQuery CLI로 분석 쿼리 실행 |
| `Bash(dbt run:*)` | dbt 모델 빌드 |
| ... | ... |

### 거부 규칙 (deny) 근거
| 규칙 | 차단 이유 |
|------|----------|
| `Bash(git push --force:*)` | 히스토리 파괴 방지 |
| `Bash(bq rm:*)` | 데이터 테이블 실수 삭제 방지 |
| ... | ... |

## GitHub Actions permissions — CI 환경

### 로컬 vs CI 권한 비교
| 항목 | 로컬 (settings.json) | CI (YAML permissions:) |
|------|---------------------|------------------------|
| git push | allow (개발자 리뷰 후 Push) | contents: write (자동 PR 브랜치) |
| 이슈 관리 | 직접 gh CLI 실행 | issues: write |
| 제한 수준 | 중간 (개발자가 즉시 오류 확인 가능) | 엄격 (자동 실행으로 오류 확산 위험) |
```

다음 Claude Code 프롬프트로 권한 문서를 자동 생성합니다:

```bash
claude "현재 .claude/settings.json의 permissions 섹션을 분석하고,
evidence/module-3-permissions-rationale.md 파일을 생성해줘.

포함할 내용:
1. 각 allow 규칙의 필요한 이유 (표 형식)
2. 각 deny 규칙의 차단 이유 (표 형식)
3. 로컬 개발 환경 vs CI 환경 권한 비교 (표 형식)
4. GitHub Actions permissions: 키의 각 항목별 근거

각 근거는 '이 작업이 없으면 X 단계에서 Y가 실패한다'는 형식으로 구체적으로 작성해줘."
```

**활동 5: 로컬 vs CI 다중 환경 권한 정책 설계** *(예상 소요: 15~20분)*

데이터 분석 팀의 실제 운영 환경에서는 동일한 에이전트 코드가 두 가지 맥락에서 실행됩니다:

| 실행 맥락 | 설명 | 권한 설계 방향 |
|-----------|------|---------------|
| **개발자 로컬** | 분석가가 탐색적 분석 또는 하니스 개발 시 Claude Code 대화형 사용 | 더 많은 도구 허용, 빠른 반복 개발 지원 |
| **CI/CD 파이프라인** | GitHub Actions에서 이슈 라벨 트리거로 자동 실행 | 최소 권한, 명시적 단계, 감사 추적 |

**다중 환경 권한 설계 패턴**:

```bash
# 로컬 개발자용 설정 (.claude/settings.json) - 팀 공유
claude "현재 .claude/settings.json의 allow 목록에 개발 편의를 위한 추가 권한을 검토해줘.
예: git log, git diff, git status, python, uv 실행 등 분석 개발에 유용한 명령들.
단, deny 목록은 로컬에서도 동일하게 유지해야 해."

# CI 파이프라인에서는 GitHub Actions permissions: 키로 별도 제어
# 에이전트 코드 자체는 동일하지만, 실행 컨텍스트의 권한이 다름
```

> **설계 원칙**: `deny` 목록은 로컬과 CI 모두에서 동일하게 유지합니다. "로컬에서도 force push는 안 됩니다." `allow` 목록은 CI에서 더 제한적일 수 있습니다 — CI 환경에서 불필요한 탐색적 명령(예: `git log`, `python 스크립트`)이 실행될 필요가 없기 때문입니다.

**활동 6: 권한 경계 종합 테스트 및 회고** *(예상 소요: 10~15분)*

현재까지 구현한 권한 정책 전체를 검증합니다:

```bash
# 전체 권한 정책 검증 체크리스트
echo "=== 권한 정책 검증 ==="

# 1. JSON 문법 검증
python -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 유효" || echo "❌ JSON 문법 오류"

# 2. allow 규칙 수 확인
ALLOW_COUNT=$(python -c "import json; d=json.load(open('.claude/settings.json')); print(len(d.get('permissions',{}).get('allow',[])))")
echo "허용 규칙 수: $ALLOW_COUNT (최소 3개 권장)"

# 3. deny 규칙 수 확인
DENY_COUNT=$(python -c "import json; d=json.load(open('.claude/settings.json')); print(len(d.get('permissions',{}).get('deny',[])))")
echo "거부 규칙 수: $DENY_COUNT (최소 3개 권장)"

# 4. 필수 deny 규칙 존재 여부 확인
python -c "
import json
d = json.load(open('.claude/settings.json'))
deny = d.get('permissions', {}).get('deny', [])
required = ['git push --force', 'bq rm', 'rm -rf']
for r in required:
    found = any(r in rule for rule in deny)
    print(f'{'✅' if found else '❌'} deny에 {r!r} 포함: {found}')
"
```

회고 질문을 `evidence/module-3-permissions-retrospective.md`에 기록합니다:

1. 권한 정책을 설계하는 과정에서 가장 판단하기 어려웠던 부분은 무엇인가? (예: 어떤 명령을 allow에 넣어야 할지 vs deny에 넣어야 할지)
2. 모듈 1에서 이미 기초적인 권한을 설정했는데, 이 모듈에서 추가적으로 설계한 부분은 무엇인가?
3. GitHub Actions의 `permissions:` 키와 Claude Code의 `permissions.allow/deny`가 서로 어떻게 보완적으로 작동하는지 한 문단으로 설명하라.

#### 자기 점검 체크리스트

> **사용 방법**: 각 항목은 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다.
> - ✅ **합격**: 성공 기준을 충족하면 체크박스에 표시하고 다음 항목으로 진행합니다.
> - ❌ **불합격**: 성공 기준을 충족하지 못하면 "실패 시 조치"를 따라 문제를 해결한 뒤 재확인합니다.
> - **진행 조건**: 5개 항목 **모두 합격(✅)** 이어야 모듈 4로 진행할 수 있습니다.

##### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | 권한 정책이 포함된 settings.json | `.claude/settings.json` — allow ≥3개, deny ≥3개 | 하니스 설정 |
| 2 | 권한 설계 근거 문서 | `evidence/module-3-permissions-rationale.md` | 하니스 문서화 |
| 3 | GitHub Actions 권한 키 포함 YAML | `.github/workflows/auto-analyze.yml` (초안 또는 완성본) | 하니스 설정 |
| 4 | 권한 경계 검증 결과 | 터미널 출력 또는 스크린샷 | 검증 증거 |
| 5 | 회고 문서 | `evidence/module-3-permissions-retrospective.md` | 학습 기록 |

### 자가 점검

**[점검 1/5] 허용/거부 규칙 구현 확인**

- [ ] `.claude/settings.json`에 `permissions.allow`와 `permissions.deny`가 각각 3개 이상의 규칙을 포함하고 있는가?
  - **검증 명령**: `python -m json.tool .claude/settings.json | grep -c '"Bash'` 출력이 6 이상인지 확인 (allow 3개 + deny 3개)
  - **✅ 합격 기준**: `python -m json.tool .claude/settings.json` 실행 시 JSON 문법 오류 없음, allow와 deny 각각 3개 이상 규칙 존재
  - **❌ 불합격 시 조치**: 활동 2, 3의 예시 JSON을 참고하여 규칙 추가 → `python -m json.tool`로 문법 재확인

**[점검 2/5] 거부 규칙 동작 검증**

- [ ] `claude "git push --force origin main을 실행해줘"` 실행 시 에이전트가 실행을 거부하는가?
  - **검증 명령**: 위 claude 명령 실행 후 출력 확인
  - **✅ 합격 기준**: 출력에 "Permission denied", "허용되지 않", "차단", "cannot" 중 하나 이상의 거부 표현이 포함됨 (실제 `git push --force`가 실행되지 않음)
  - **❌ 불합격 시 조치**: `.claude/settings.json`의 deny 목록에 `"Bash(git push --force:*)"` 항목 존재 여부 확인 → Claude Code 세션 재시작 후 재시도

**[점검 3/5] GitHub Actions 권한 키 설정**

- [ ] `.github/workflows/auto-analyze.yml`에 `permissions:` 섹션이 존재하며, `issues: write`와 `contents: write`가 포함되어 있는가?
  - **검증 명령**: `grep -A 5 'permissions:' .github/workflows/auto-analyze.yml`
  - **✅ 합격 기준**: 출력에 `issues: write`와 `contents: write` 두 항목이 모두 포함됨
  - **❌ 불합격 시 조치**: 워크플로 YAML의 `jobs.<job-id>:` 섹션 아래에 활동 4의 권한 설정 추가 (워크플로 전체 작성은 모듈 4에서 완성)

**[점검 4/5] 권한 설계 근거 문서화**

- [ ] `evidence/module-3-permissions-rationale.md`가 존재하며, 로컬 환경과 CI 환경의 권한 비교 섹션이 포함되어 있는가?
  - **검증 명령**: `ls -la evidence/module-3-permissions-rationale.md && grep -c "로컬\|CI\|GitHub Actions" evidence/module-3-permissions-rationale.md`
  - **✅ 합격 기준**: 파일이 존재하고, "로컬", "CI", "GitHub Actions" 중 적어도 두 단어가 파일 내에 포함됨
  - **❌ 불합격 시 조치**: 활동 4의 Claude Code 프롬프트를 실행하여 문서 자동 생성

**[점검 5/5] 핵심 개념 이해 확인**

- [ ] 다음 두 권한 체계의 차이를 명확히 설명할 수 있는가: (A) `.claude/settings.json`의 `permissions.allow/deny` vs (B) GitHub Actions의 `permissions:` 키
  - **검증 방법**: 아래 질문에 대한 답을 직접 작성한 뒤 정답 예시와 비교
  - **✅ 합격 기준**: "A는 에이전트가 실행할 수 있는 셸 명령/도구 범위를 제어하고, B는 GitHub Actions 워크플로가 GitHub API에 접근할 수 있는 범위를 제어한다"는 내용이 답변에 포함됨

  > **직접 작성할 답변 공간:**
  > - A(`permissions.allow/deny`)가 제어하는 것: _(직접 작성)_
  > - B(GitHub Actions `permissions:`)가 제어하는 것: _(직접 작성)_
  > - 두 권한 체계가 함께 필요한 이유: _(직접 작성)_
  >
  > ❌ 불합격 시 조치: 핵심 개념의 "Claude Code 권한 계층 구조"와 "GitHub Actions `permissions:` 키" 섹션을 다시 읽고 답변 수정

> **모듈 진행 조건**: 위 5개 항목 **전부 ✅ 합격** 후 `modules/module-4.md`로 진행하세요.
> 상세 실습 가이드: `modules/module-3.md` 참조

---

## 모듈 4: 종단간 에이전트 기반 데이터 분석 워크플로 — 하니스 전체 통합 및 실행

**총 학습 시간**: 2.5~3.5시간

| 활동 | 내용 | 예상 시간 |
|------|------|-----------|
| 활동 1 | 하니스 구성 요소 통합 검증 — 모듈 1~3 결과물 사전 점검 | 15~20분 |
| 활동 2 | GitHub Actions 7단계 오케스트레이션 워크플로 YAML 작성 | 30~40분 |
| 활동 3 | 에이전트 단계별 프롬프트 파일 7개 설계 | 25~30분 |
| 활동 4 | 전체 파이프라인 종단간 실행 — DAU/MAU 분석 이슈에서 PR까지 | 20~25분 |
| 활동 5 | 의도적 오류 발생 및 `stage:error` 라벨 기반 복구 실습 | 15~20분 |
| 활동 6 | 파이프라인 비용 측정, 하니스 효과 회고 및 문서화 | 20~25분 |

### 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

- GitHub Issue에 `auto-analyze` 라벨을 부착한 뒤 `gh run watch`로 실시간 모니터링하여, 이슈 라벨이 `stage:1-parse` → `stage:2-define` → … → `done` 순서로 전환되는 것을 이슈 타임라인에서 확인하고, dbt 모델 + marimo 노트북 소스를 포함한 PR이 자동 생성되는 것을 `gh pr list --label "auto-analyzed"` 출력으로 증명할 수 있다 *(검증: `gh issue view <NUMBER> --json labels,timelineItems` 출력 및 PR 링크)*
- 7단계 파이프라인의 각 단계 완료 증거(`<!-- stage:N-complete -->` HTML 앵커)가 이슈 코멘트에 순서대로 존재함을 `gh issue view <NUMBER> --comments | grep "stage:.*-complete"` 출력으로 확인할 수 있다 *(검증: 터미널 출력에 `stage:1-complete`부터 `stage:7-complete`까지 7개 앵커 존재)*
- `GCP_SA_KEY`를 의도적으로 무효화하여 `stage:5-extract`에서 INFRA 오류를 발생시키고, 이슈 코멘트의 `<!-- error-category: INFRA -->` 앵커를 확인한 뒤, Secret 복구 → `stage:error` 라벨 제거 → `stage:5-extract` 재부착으로 파이프라인이 해당 단계부터 재개되는 것을 검증할 수 있다 *(검증: `gh issue view <NUMBER> --comments | grep -A 3 "error-category"` 출력)*
- `evidence/query_cost_log.json`의 각 단계별 `estimated_bytes`를 합산하여 7단계 파이프라인 1회 실행의 총 BigQuery 비용을 달러로 환산하고, 이 수치가 `AGENTS.md`의 비용 정책(1GB 제한)과 일치하는지 서면으로 설명할 수 있다 *(검증: `evidence/module-4-retrospective.md`의 BigQuery 비용 실측 항목)*

#### 핵심 개념

**종단간(End-to-End) 에이전트 기반 데이터 분석 워크플로란?**

> **종단간 워크플로 (end-to-end workflow)**: 사람이 분석 요청(이슈)을 생성하고 결과(PR + 리포트)를 받는 것 사이의 모든 단계가, 모듈 1~3에서 구축한 하니스(훅·설정·권한·슬래시 커맨드) 위에서 에이전트에 의해 자동으로 수행되는 파이프라인 — 최초 사용 시 명확히 구분할 개념

이 모듈은 모듈 0~3에서 구축한 하니스의 **모든 구성 요소가 함께 동작하는 종합 검증 단계**입니다:

| 모듈 | 구축한 하니스 구성 요소 | 모듈 4에서의 역할 |
|------|----------------------|-----------------|
| 모듈 0 | BigQuery, dbt, marimo 환경 | 에이전트가 사용하는 데이터/도구 인프라 |
| 모듈 1 | 훅(`bq-cost-guard.sh`, dbt 컴파일 훅) + `AGENTS.md` | 각 파이프라인 단계에서 자동 정책 실행 |
| 모듈 2 | 슬래시 커맨드(`/analyze`, `/validate`) | 에이전트가 작업 명세를 일관되게 따르는 기반 |
| 모듈 3 | 권한 정책(`permissions.allow/deny`, GitHub Actions `permissions:`) | 에이전트가 파이프라인 내에서 적절한 권한으로만 작동 |
| **모듈 4** | **GitHub Actions YAML + 7단계 프롬프트** | 위 모든 구성 요소를 자동으로 연결하고 실행 |

**7단계 워크플로 — 이슈에서 PR까지**

| 단계 | 라벨 | 에이전트 작업 | 생성 산출물 |
|------|------|--------------|------------|
| 진입 | `auto-analyze` | 워크플로 시작 (수동 부착) | — |
| 1 | `stage:1-parse` | 이슈 본문 파싱, 구조화된 요청 객체 생성 | 파싱 결과 코멘트 |
| 2 | `stage:2-define` | 비즈니스 질문 → 분석 질문 변환, `problem_statement.md` 작성 | 문제 정의서 |
| 3 | `stage:3-deliverables` | 필요 데이터/차트/테이블 목록 정의 | 산출물 체크리스트 |
| 4 | `stage:4-spec` | dbt 쿼리 계획, marimo 구조 설계 | 분석 스펙 문서 |
| 5 | `stage:5-extract` | dbt 실행, BigQuery 쿼리, 데이터 추출 | dbt 결과, 데이터 파일 |
| 6 | `stage:6-analyze` | marimo 노트북 작성, 분석·시각화 수행 | marimo `.py` 소스 |
| 7 | `stage:7-report` | HTML/PDF 내보내기, PR 자동 생성 | PR + 리포트 아티팩트 |
| 완료 | `done` | 이슈 자동 닫기 | — |

**라벨 연쇄 전환(Label Chaining) 메커니즘**

각 단계가 완료되면 현재 라벨을 제거하고 다음 단계 라벨을 부착합니다. 이 라벨 부착 이벤트가 GitHub Actions의 `on.issues.types: [labeled]` 트리거를 다시 발생시켜, 다음 단계 워크플로가 연쇄적으로 트리거됩니다:

```yaml
# 라벨 전환 메커니즘 (개념도)
on:
  issues:
    types: [labeled]  # 어떤 라벨이든 부착되면 워크플로 트리거

jobs:
  orchestrate:
    if: |
      github.event.label.name == 'auto-analyze' ||
      startsWith(github.event.label.name, 'stage:')
    steps:
      # 1. 현재 라벨에 맞는 단계 에이전트 실행
      # 2. 산출물을 이슈 코멘트에 <!-- stage:N-complete --> 앵커와 함께 기록
      # 3. 현재 라벨 제거 + 다음 단계 라벨 부착 → labeled 이벤트 재발생
```

> 🔧 **하니스 vs 산출물**: GitHub Actions YAML 파일(`.github/workflows/auto-analyze.yml`)은 **하니스 설정**입니다. 이 파일이 생성하는 것(DAU 분석 marimo 노트북, HTML 리포트, PR)이 **파이프라인 산출물**입니다.

**오류 처리 전략**

자동화 파이프라인에서 오류는 불가피합니다. 4가지 카테고리로 분류하고, 각 카테고리별로 자동 재시도 또는 사람 개입이 필요한지 판단합니다:

| 카테고리 | 코드 | 예시 | 자동 재시도 |
|----------|------|------|-------------|
| 인프라 오류 | `INFRA` | BigQuery 인증 실패, GitHub API rate limit | ✅ (최대 3회) |
| 데이터 오류 | `DATA` | 테이블 미존재, dbt 테스트 실패 | ❌ (데이터 확인 필요) |
| 에이전트 오류 | `AGENT` | 잘못된 SQL 생성, marimo 실행 오류 | ✅ (최대 2회, 프롬프트 보강 후) |
| 워크플로 오류 | `WORKFLOW` | 라벨 전환 실패, permissions 누락 | ❌ (워크플로 수정 필요) |

### 활동

**활동 1: 하니스 구성 요소 통합 검증** *(예상 소요: 15~20분)*

> 🔧 **이 활동의 목적**: 모듈 4에서 전체 파이프라인을 실행하기 전에, 모듈 1~3에서 구축한 하니스가 모두 올바르게 설정되어 있는지 검증합니다. 이것이 "종단간 파이프라인의 전제 조건 점검"입니다.

```bash
# 모듈 1~3 구성 요소 통합 점검
echo "=== 하니스 구성 요소 통합 점검 ==="

# 모듈 1 확인: 훅 스크립트 존재
echo "[모듈 1] 훅 스크립트..."
ls -la scripts/hooks/bq-cost-guard.sh 2>/dev/null && echo "✅ bq-cost-guard.sh 존재" || echo "❌ bq-cost-guard.sh 없음"

# 모듈 1 확인: settings.json 존재 및 훅 등록
echo "[모듈 1] settings.json 훅 설정..."
python -c "import json; d=json.load(open('.claude/settings.json')); print('✅ hooks 존재' if 'hooks' in d else '❌ hooks 없음')"

# 모듈 2 확인: 슬래시 커맨드 파일 존재
echo "[모듈 2] 슬래시 커맨드..."
ls .claude/commands/*.md 2>/dev/null && echo "✅ 커맨드 파일 존재" || echo "❌ .claude/commands/*.md 없음"

# 모듈 3 확인: 권한 정책 적용
echo "[모듈 3] 권한 정책..."
python -c "
import json
d = json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
allow_count = len(p.get('allow', []))
deny_count = len(p.get('deny', []))
print(f'✅ allow {allow_count}개, deny {deny_count}개' if allow_count >= 3 and deny_count >= 3 else f'❌ allow {allow_count}개, deny {deny_count}개 (각 3개 이상 필요)')
"

# GitHub Secrets 확인
echo "[모듈 0] GitHub Secrets..."
gh secret list | grep -E "GCP_SA_KEY|GCP_PROJECT_ID|CLAUDE_TOKEN" | wc -l | xargs echo "✅ Secrets 등록 수:"
```

**활동 2: GitHub Actions 7단계 오케스트레이션 워크플로 YAML 작성** *(예상 소요: 30~40분)*

> 💰 **BigQuery 비용**: 워크플로 YAML 작성 자체는 비용이 발생하지 않습니다. 실제 비용은 활동 4에서 파이프라인 실행 시 발생합니다 (합성 데이터 ~100MB 기준 전체 파이프라인 예상 비용: $0.01~$0.05).

다음 Claude Code 프롬프트로 워크플로 YAML을 처음부터 작성합니다:

```bash
claude "AGENTS.md와 .claude/settings.json을 읽고,
.github/workflows/auto-analyze.yml 파일을 처음부터 작성해줘.

요구사항:
- 트리거: issues 이벤트, labeled 액션
- 실행 조건: auto-analyze 라벨 또는 stage: 접두어 라벨
- 환경: ubuntu-latest, Python 3.12, uv, dbt-bigquery
- 인증: claude setup-token (CLAUDE_TOKEN), GCP 서비스 계정 (GCP_SA_KEY)
- GitHub Actions permissions: issues: write, contents: write, pull-requests: write
- 7단계 라벨별 분기: stage:1-parse ~ stage:7-report
- 각 단계: Claude Agent SDK로 .claude/prompts/stage-N-*.md 프롬프트 실행
- 각 단계 완료: 이슈 코멘트 작성 (<!-- stage:N-complete --> 앵커 포함) + 라벨 전환
- 오류 시: stage:error 라벨 부착 + 오류 코멘트 작성 (<!-- error-category: ... --> 앵커 포함)
- stage:7-report: HTML/PDF 아티팩트 업로드, auto-analyzed 라벨 포함 PR 생성

작성 후 actionlint로 문법 검증하고, 오류가 있으면 수정해줘."
```

**워크플로 라벨 11개 사전 등록**:

```bash
# 7단계 워크플로 라벨 일괄 생성
gh label create "auto-analyze" --color "0E8A16" --description "자동 분석 워크플로 진입점"
gh label create "stage:1-parse" --color "1D76DB" --description "단계 1: 이슈 파싱"
gh label create "stage:2-define" --color "1D76DB" --description "단계 2: 문제 정의"
gh label create "stage:3-deliverables" --color "1D76DB" --description "단계 3: 산출물 명세"
gh label create "stage:4-spec" --color "1D76DB" --description "단계 4: 스펙 작성"
gh label create "stage:5-extract" --color "5319E7" --description "단계 5: 데이터 추출"
gh label create "stage:6-analyze" --color "5319E7" --description "단계 6: 분석 수행"
gh label create "stage:7-report" --color "5319E7" --description "단계 7: 리포트 생성"
gh label create "done" --color "0E8A16" --description "워크플로 완료"
gh label create "stage:error" --color "D93F0B" --description "단계 실행 오류"
gh label create "needs-retry" --color "FBCA04" --description "재시도 필요"

# 라벨 등록 확인
gh label list | grep -cE "auto-analyze|stage:|^done|needs-retry"
# 기대 출력: 11
```

> **색상 규칙**: 초록(`0E8A16`) = 진입/완료, 파랑(`1D76DB`) = 설계 단계(1-4), 보라(`5319E7`) = 실행 단계(5-7), 빨강(`D93F0B`) = 오류, 노랑(`FBCA04`) = 주의

**활동 3: 에이전트 단계별 프롬프트 파일 7개 설계** *(예상 소요: 25~30분)*

각 파이프라인 단계에서 Claude Agent SDK가 참조하는 프롬프트 파일을 설계합니다:

```bash
# 7단계 프롬프트 파일 일괄 생성
claude "AGENTS.md를 읽고, .claude/prompts/ 디렉토리에
stage-1-parse.md부터 stage-7-report.md까지 7개 파일을 생성해줘.

각 파일의 구조:
## 컨텍스트
- 이전 단계 산출물 위치 (이슈 코멘트의 <!-- stage:N-complete --> 앵커)
- AGENTS.md의 핵심 규약 요약 (인라인)

## 작업 지시
- 구체적 작업 단계 (순서 있는 목록)
- 각 단계의 성공 기준 (기계적으로 검증 가능한 형식)

## 산출물
- 생성할 파일 경로와 형식
- 이슈 코멘트로 기록할 내용 (<!-- stage:N-complete --> 앵커 포함)

## 제약 조건
- BigQuery 비용 제한: 단계 5의 각 쿼리는 1GB 미만 스캔
- AGENTS.md 규약: dbt mart 레이어만 참조, staging 직접 참조 금지
- marimo 규약: 첫 셀에 데이터 소스 선언 필수

생성 후 각 파일의 핵심 내용을 요약해줘."
```

**단계별 프롬프트 설계 원칙**:

| 단계 | 가장 중요한 제약 조건 | 이유 |
|------|-------------------|----|
| 1 (파싱) | 이슈 본문 형식 준수 | 후속 단계가 파싱 결과에 의존 |
| 2 (문제 정의) | 비즈니스 의도 유지 | 잘못된 분석 방향 방지 |
| 3 (산출물 명세) | 구체적 파일 경로와 형식 | 단계 6, 7에서 파일을 찾을 수 있어야 함 |
| 4 (스펙 작성) | BigQuery 쿼리 계획을 dry-run으로 비용 사전 확인 | 단계 5 실행 전 비용 통제 |
| 5 (데이터 추출) | 1GB 비용 제한 + dbt 테스트 통과 확인 | 가장 비용이 큰 단계 |
| 6 (분석 수행) | marimo 노트북 첫 셀 데이터 소스 선언 | 재현 가능성 보장 |
| 7 (리포트 생성) | PR 본문에 evidence/ 파일 링크 포함 | 완료 증거의 추적 가능성 |

**활동 4: 전체 파이프라인 종단간 실행** *(예상 소요: 20~25분)*

> 💰 **BigQuery 비용 추정**: 합성 데이터 기준 7단계 파이프라인 1회 실행 비용은 약 $0.01~$0.05입니다. `evidence/query_cost_log.json`에서 단계별 스캔 바이트를 실시간으로 추적합니다.

```bash
# 1. 분석 요청 이슈 생성
gh issue create \
  --title "[분석] FitTrack 2026년 1분기 DAU/MAU 트렌드 분석" \
  --body "$(cat .github/ISSUE_TEMPLATE/analysis-request.md | sed 's/---//g')" \
  --label "분석요청"

# 2. 이슈 번호 확인
ISSUE_NUMBER=$(gh issue list --label "분석요청" --limit 1 --json number -q '.[0].number')
echo "이슈 번호: #$ISSUE_NUMBER"

# 3. auto-analyze 라벨 부착 — 파이프라인 시작
gh issue edit $ISSUE_NUMBER --add-label "auto-analyze"

# 4. 워크플로 실행 실시간 모니터링
gh run watch

# 5. 이슈 라벨 전환 이력 확인
gh issue view $ISSUE_NUMBER --json labels,timelineItems
```

**관찰 초점**: 라벨이 `auto-analyze` → `stage:1-parse` → ... → `done` 순서로 정확히 전환되는가? 모듈 1에서 구현한 `bq-cost-guard.sh` 훅이 단계 5 실행 시 자동으로 작동하는가? 모듈 3에서 설계한 `permissions.allow/deny`가 에이전트의 행동을 실제로 제한하는가?

**활동 5: 의도적 오류 발생 및 복구 실습** *(예상 소요: 15~20분)*

```bash
# 1. GCP_SA_KEY를 의도적으로 무효화 (INFRA 오류 시뮬레이션)
gh secret set GCP_SA_KEY --body "invalid_key_for_testing"

# 2. stage:5-extract 라벨 부착하여 데이터 추출 단계 트리거
gh issue edit $ISSUE_NUMBER --add-label "stage:5-extract"

# 3. 오류 발생 후 이슈 코멘트 확인
gh issue view $ISSUE_NUMBER --comments | grep -A 5 "error-category"
# 기대 출력: <!-- error-category: INFRA --> 포함 코멘트

# 4. Secret 복구 후 파이프라인 재개
gh secret set GCP_SA_KEY < key.json  # 원래 키 복구

# 5. stage:error 라벨 제거 + stage:5-extract 재부착으로 재개
gh issue edit $ISSUE_NUMBER --remove-label "stage:error"
gh issue edit $ISSUE_NUMBER --add-label "stage:5-extract"
```

> **복구 원칙**: `stage:error` 라벨을 제거하고 실패한 단계의 라벨을 재부착하면, 파이프라인이 해당 단계부터 재개됩니다. 이전 단계를 다시 실행하지 않으므로, 이미 완료된 단계의 산출물이 이슈 코멘트에 남아 있어야 합니다.

**활동 6: 파이프라인 비용 측정, 하니스 효과 회고 및 문서화** *(예상 소요: 20~25분)*

```bash
# BigQuery 비용 측정
python3 -c "
import json

# evidence/query_cost_log.json에서 단계별 비용 집계
with open('evidence/query_cost_log.json') as f:
    log = json.load(f)

total_bytes = sum(entry.get('estimated_bytes', 0) for entry in log)
total_cost_usd = total_bytes / (1024**4) * 5  # on-demand: $5/TB

print(f'총 스캔 데이터: {total_bytes / (1024**3):.2f} GB')
print(f'총 비용 (on-demand): \${total_cost_usd:.4f}')
print(f'비용 정책 (1GB 제한): {\"✅ 준수\" if total_bytes < 1024**3 else \"❌ 초과\"}')
"
```

**관찰-수정-창작 사이클**: 전체 파이프라인 실행을 관찰한 결과를 바탕으로 `evidence/module-4-retrospective.md`를 작성합니다:

```markdown
## 파이프라인 실행 회고 — 영역 A: 하니스 통합 효과

1. 모듈 1~3에서 구축한 하니스 구성 요소(훅, 권한, 슬래시 커맨드) 중
   파이프라인 실행 중 실제로 동작했음을 확인한 것은?
   - 훅 동작 여부: (예: bq-cost-guard.sh가 stage:5에서 실행됨)
   - 권한 거부 여부: (예: deny 규칙이 특정 명령을 차단했는가?)
   - 슬래시 커맨드 사용 여부: (프롬프트에서 커맨드를 참조했는가?)

## 영역 B: 파이프라인 안정성

2. 사람 개입 없이 7단계 전체를 완료한 횟수:
   - 시도 횟수: ___ 회
   - 성공 횟수: ___ 회 (자동 완료율: ___%)
   
3. 가장 많이 실패한 단계와 원인:
   - 단계: stage:N-___
   - 원인 카테고리: INFRA / DATA / AGENT / WORKFLOW

## 영역 C: BigQuery 비용 실측

4. 7단계 파이프라인 1회 실행 총 비용:
   - 총 스캔 데이터: ___ GB
   - 총 비용: $___
   - 비용 정책(1GB 제한) 준수 여부: ✅ / ❌
```

**하니스 생성**: 회고 결과를 바탕으로 다음을 실행합니다:
1. 가장 많이 실패한 단계의 `.claude/prompts/stage-N-*.md` 프롬프트에 명시적 제약 조건 추가
2. `AGENTS.md`에 "파이프라인 운영 중 발견된 실수" 섹션 추가
3. 비용이 예상보다 높은 단계가 있으면 해당 단계의 쿼리를 최적화하고 `bq-cost-guard.sh`의 임계값 재검토

#### 자기 점검 체크리스트

> **사용 방법**: 각 항목은 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다.
> - ✅ **합격**: 성공 기준을 충족하면 체크박스에 표시하고 다음 항목으로 진행합니다.
> - ❌ **불합격**: 성공 기준을 충족하지 못하면 "실패 시 조치"를 따라 문제를 해결한 뒤 재확인합니다.
> - **코스 완료 조건**: 7개 항목 **전부 합격(✅)** 이어야 코스를 완료한 것으로 인정됩니다.

##### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | GitHub Actions 워크플로 YAML | `.github/workflows/auto-analyze.yml` — 7단계 라벨 분기 + 오류 처리 포함 | 하니스 설정 |
| 2 | 워크플로 라벨 11개 | GitHub 레포 라벨 — `auto-analyze`, `stage:1-parse` ~ `stage:7-report`, `done`, `stage:error`, `needs-retry` | 하니스 설정 |
| 3 | 에이전트 단계별 프롬프트 7개 | `.claude/prompts/stage-1-parse.md` ~ `stage-7-report.md` | 하니스 설정 |
| 4 | 자동 생성 PR | GitHub Pull Requests — dbt 모델 + marimo 소스 + HTML/PDF 아티팩트 | 파이프라인 산출물 |
| 5 | 이슈 타임라인 (단계 전환 이력) | GitHub Issue — 라벨 전환 + 각 단계 완료 코멘트 | 파이프라인 산출물 |
| 6 | BigQuery 비용 로그 | `evidence/query_cost_log.json` | 완료 증거 |
| 7 | 파이프라인 회고 문서 | `evidence/module-4-retrospective.md` — 영역 A, B, C 작성 | 학습 기록 |

### 자가 점검

**[점검 1/7] 워크플로 YAML 문법 검증**

- [ ] `.github/workflows/auto-analyze.yml` 파일이 존재하며 YAML 문법 오류가 없는가?
  - **검증 명령**: `actionlint .github/workflows/auto-analyze.yml` (또는 `python -c "import yaml; yaml.safe_load(open('.github/workflows/auto-analyze.yml'))"`)
  - **✅ 합격 기준**: actionlint 오류 없음, 파일에 `on.issues.types: [labeled]` 트리거 존재, `permissions: issues: write` 존재
  - **❌ 불합격 시 조치**: YAML 들여쓰기 오류(탭 대신 스페이스), 따옴표 미닫힘, `if:` 조건 문법 오류 순서로 확인

**[점검 2/7] 워크플로 라벨 등록 확인**

- [ ] 11개 워크플로 라벨(`auto-analyze`, `stage:1-parse` ~ `stage:7-report`, `done`, `stage:error`, `needs-retry`)이 모두 등록되어 있는가?
  - **검증 명령**: `gh label list | grep -cE "auto-analyze|stage:|^done|needs-retry"`
  - **✅ 합격 기준**: 출력이 `11`
  - **❌ 불합격 시 조치**: `gh label list`에서 누락된 라벨 확인 후 활동 2의 `gh label create` 명령으로 개별 생성

**[점검 3/7] 파이프라인 자동 트리거 확인**

- [ ] GitHub Issue에 `auto-analyze` 라벨을 붙였을 때 GitHub Actions가 30초 이내에 자동 트리거되는가?
  - **검증 명령**: `gh issue edit <NUMBER> --add-label "auto-analyze"` 후 `gh run list --workflow=auto-analyze.yml`로 실행 기록 확인
  - **✅ 합격 기준**: 라벨 부착 후 30초~2분 이내에 워크플로 실행이 시작됨 (`In progress` 상태)
  - **❌ 불합격 시 조치**: 워크플로 파일의 `on.issues.types: [labeled]` 설정 확인, 레포 Settings > Actions > General에서 Actions 활성화 여부 확인

**[점검 4/7] 이슈 라벨 순차 전환 확인**

- [ ] 파이프라인 완료 후 이슈 타임라인에서 `auto-analyze` → `stage:1-parse` → ... → `done` 순서로 라벨 전환 이벤트가 기록되어 있는가?
  - **검증 명령**: `gh issue view <NUMBER> --json timelineItems | python -m json.tool | grep -E "label|name"`
  - **✅ 합격 기준**: 타임라인에 7개 단계 라벨 전환 이벤트가 순서대로 기록됨, 마지막에 `done` 라벨 부착 이벤트 존재
  - **❌ 불합격 시 조치**: 특정 단계에서 멈춘 경우, 해당 단계의 Actions 로그에서 라벨 전환 단계 오류 확인, `issues: write` 권한 설정 재확인

**[점검 5/7] 자동 생성 PR 확인**

- [ ] 파이프라인 완료 후 dbt 모델과 marimo 노트북을 포함한 PR이 자동 생성되어 있는가?
  - **검증 명령**: `gh pr list --label "auto-analyzed"` 실행 후 PR 확인, `gh pr view <PR_NUMBER>` 출력에서 "분석 요약" 섹션 확인
  - **✅ 합격 기준**: PR이 존재하고 `analyses/analysis_*.py` 또는 `models/*.sql` 파일이 Files changed에 포함됨, PR 본문에 분석 요약과 `evidence/` 파일 링크 존재
  - **❌ 불합격 시 조치**: stage:7-report 단계의 `git add`, `git commit`, `gh pr create` 명령 오류 로그 확인, `GITHUB_PAT` Secret(또는 `contents: write` 권한) 유효성 검증

**[점검 6/7] HTML/PDF 리포트 아티팩트 확인**

- [ ] HTML/PDF 리포트가 GitHub Actions 아티팩트로 생성되어 다운로드 가능한가?
  - **검증 명령**: GitHub Actions 실행 결과 페이지 하단의 Artifacts 섹션 확인 (또는 `gh run download <RUN_ID>`)
  - **✅ 합격 기준**: Artifacts 섹션에 `analysis-report` 항목이 존재하고, 다운로드 시 `.html`과 `.pdf` 파일 중 적어도 하나가 포함됨
  - **❌ 불합격 시 조치**: `marimo export html` / `marimo export pdf` 명령의 터미널 출력 오류 확인, `upload-artifact` GitHub Actions 단계의 `path:` 설정이 실제 파일 경로와 일치하는지 확인

**[점검 7/7] BigQuery 비용 정책 준수 확인**

- [ ] `evidence/query_cost_log.json`에 단계별 스캔 바이트가 기록되어 있으며, 총 비용이 BigQuery 1GB 제한 정책을 준수하는가?
  - **검증 명령**: `python3 -c "import json; log=json.load(open('evidence/query_cost_log.json')); total=sum(e.get('estimated_bytes',0) for e in log); print(f'총 스캔: {total/1024**3:.2f}GB, 비용: \${total/1024**4*5:.4f}')"`
  - **✅ 합격 기준**: 파일이 존재하고, 총 스캔 데이터가 1GB 미만, 각 단계의 `estimated_bytes` 필드가 존재함
  - **❌ 불합격 시 조치**: `evidence/query_cost_log.json`이 없으면 `bq-cost-guard.sh` 훅이 실제로 실행되었는지 확인 → 훅이 실행되지 않았다면 settings.json의 `PreToolUse` 훅 설정 재확인

> **코스 완료 조건**: 위 7개 항목 **전부 ✅ 합격** 시 코스를 완료한 것으로 인정됩니다.
> 상세 실습 가이드: `modules/module-4.md` 참조

#### 코스 마무리

##### 학습 요약

| 모듈 | 구축한 하니스 구성 요소 | 핵심 역량 |
|------|----------------------|-----------|
| 0 | 개발 환경 (BigQuery, dbt, marimo, Claude Code) | 도구 설치, 데이터 준비 |
| 1 | 훅(`PreToolUse`, `PostToolUse`, `Stop`) + `AGENTS.md` | settings.json으로 에이전트 정책 구현 |
| 2 | 슬래시 커맨드(`/analyze`, `/validate`, `/check-cost`) | 에이전트 작업 명세화 |
| 3 | 권한 정책(`permissions.allow/deny`, GitHub Actions `permissions:`) | 에이전트 경계 설계 |
| 4 | GitHub Actions 7단계 오케스트레이션 워크플로 | 종단간 자동 데이터 분석 파이프라인 |

##### 다음 단계 제안

이 코스에서 학습한 하니스 엔지니어링을 실무에 적용할 때:

1. **작게 시작하세요**: `AGENTS.md`(스캐폴딩)부터 시작하고, 반복적인 작업에 훅과 커맨드를 추가하며, 안정화된 후 GitHub Actions 오케스트레이션을 도입하세요.

2. **권한 정책부터 설계하세요**: 실무 환경에서는 프로덕션 데이터 접근이 있으므로 `permissions.deny`에 되돌리기 어려운 작업(테이블 삭제, 스키마 변경, force push)을 먼저 차단하세요.

3. **비용을 측정하세요**: BigQuery on-demand 환경에서는 각 쿼리의 스캔 바이트를 `bq-cost-guard.sh`로 추적하고, 월간 비용 예산을 `AGENTS.md`에 명시하세요.

4. **점진적으로 자율성을 부여하세요**: 완전 자동화 가능한 작업(기계적으로 검증 가능한 작업)부터 시작하고, 에이전트의 성공률이 90% 이상일 때 더 복잡한 작업으로 확장하세요.


---

## 모듈 간 학습 흐름

```
모듈 0: 환경 설정 (BigQuery, dbt, marimo, Claude Code, AGENTS.md 초안)
  ↓
모듈 1: 훅과 설정 엔지니어링 (.claude/settings.json, hooks, permissions)
  ↓ 에이전트가 "안전하게" 작업할 수 있는 정책 경계
모듈 2: 슬래시 커맨드 작성 (.claude/commands/*.md, $ARGUMENTS, 완료 증거)
  ↓ 에이전트가 "일관되게" 작업할 수 있는 명세 레이어
모듈 3: 권한 오케스트레이션 (.claude/settings.json permissions.allow/deny, GitHub Actions permissions:)
  ↓ 에이전트가 "안전한 경계 내에서만" 작업할 수 있는 권한 정책
모듈 4: 종단간 에이전트 기반 데이터 분석 워크플로 (GitHub Actions + Claude Agent SDK, 이슈 → PR)
  ↓ 모든 하니스 구성 요소를 통합하여 자동 파이프라인 완성
```

### 3단계 학습 사이클 템플릿: 관찰-수정-창작

각 모듈(모듈 1~4)은 아래 **관찰(observe) → 수정(modify) → 창작(create)** 사이클을 반복합니다. 모듈 0(환경 설정)은 오리엔테이션 모듈로서 ## 개요, ## 설치, ## 개념 소개 구조를 사용하며 이 사이클 대상에서 제외됩니다.

> **핵심 원리**: 하니스 컴포넌트는 이론이 아니라 **직접 관찰한 문제**에서 출발합니다. 에이전트의 행동을 먼저 관찰하고, 기존 하니스 컴포넌트를 수정하며 원인을 파악한 뒤, 재발 방지를 위한 새로운 컴포넌트를 창작합니다.

---

#### Phase 1: 관찰 (Observe)

**정의**: 수강생이 Claude Code 에이전트와 함께 실제 데이터 분석 작업을 수행하며, 에이전트의 행동 패턴 — 성공, 실패, 예상치 못한 결과 — 을 직접 관찰하는 단계입니다. 에이전트가 어떻게 동작하는지 지켜보고, 무엇이 일어나는지 기록합니다.

**목적**: 에이전트의 현재 능력 범위와 한계를 체감하여, 이후 수정과 창작의 구체적 근거를 확보합니다.

| 항목 | 설명 |
|------|------|
| **입력(Input)** | • 해당 모듈의 학습 목표 및 실습 가이드<br>• 스타터 레포의 dbt 모델, 합성 데이터, 이슈 템플릿<br>• 이전 모듈에서 생성한 하니스 컴포넌트 (모듈 2 이후) |
| **활동(Activity)** | • Claude Code에 분석 프롬프트를 입력하고 에이전트 행동 관찰<br>• 에이전트 출력의 정확성, 일관성, 안전성을 평가<br>• 예상과 다른 행동(누락, 오류, 과도한 자율성)을 기록 |
| **산출물(Output)** | • **관찰 로그**: 에이전트에게 지시한 프롬프트와 실제 결과를 기록한 메모<br>• **관찰 노트**: 성공/실패/예상외 행동을 분류한 목록 |

**수행 기준**:
- 최소 2회 이상의 에이전트 작업 실행을 완료할 것
- 각 실행에서 에이전트의 구체적 행동(실행한 명령, 생성한 파일, 출력 내용)을 기록할 것

**FitTrack 시나리오 예시** (모듈 1):
> Claude Code에 "FitTrack 앱의 1월 DAU를 일별로 집계해줘"라고 요청한 후, 에이전트가 `raw_events` 테이블을 직접 쿼리하는지 아니면 `stg_events` → `mart_dau` 경로를 따르는지 관찰합니다. `AGENTS.md`가 없는 상태에서 에이전트가 dbt 모델 계층을 무시하고 raw 테이블에 직접 쿼리를 실행하는 문제를 관찰합니다.

---

#### Phase 2: 수정 (Modify)

**정의**: Phase 1에서 관찰한 에이전트 행동을 분석하고, **기존 하니스 컴포넌트를 수정**하여 문제를 개선하는 단계입니다. 이미 존재하는 설정, 규칙, 훅 등을 조정하며 하니스의 작동 원리를 체득합니다.

**목적**: 관찰된 문제를 패턴으로 일반화하고, 기존 컴포넌트의 수정을 통해 "어떤 종류의 하니스 컴포넌트가 이를 방지할 수 있는가?"를 판단합니다.

| 항목 | 설명 |
|------|------|
| **입력(Input)** | • Phase 1의 관찰 로그 및 관찰 노트<br>• 해당 모듈의 수정 실습 가이드 (각 모듈 문서에 명시) |
| **활동(Activity)** | • 관찰된 문제를 **분류**(안전성, 일관성, 완전성, 효율성)하고 **우선순위** 부여<br>• 기존 하니스 컴포넌트(설정, 훅, 커맨드 등)를 수정하여 문제 개선<br>• 각 문제에 대해 "규칙/스킬/훅/워크플로 중 어느 컴포넌트로 해결 가능한가?" 매핑 |
| **산출물(Output)** | • **수정된 컴포넌트**: 기존 파일에 대한 구체적 변경 사항<br>• **문제-컴포넌트 매핑 표**: 식별된 문제 목록과 각각에 대응하는 하니스 컴포넌트 유형 |

**수정 질문 프레임워크** (모든 모듈 공통 구조):

| 질문 범주 | 질문 형식 | 목적 |
|-----------|-----------|------|
| **행동 관찰** | "에이전트가 ___ 할 때 예상과 달랐던 점은?" | 문제 식별 |
| **위험 평가** | "이 행동이 프로덕션 환경에서 발생하면 어떤 결과를 초래하는가?" | 심각도 판단 |
| **원인 분석** | "에이전트가 이렇게 행동한 이유는 컨텍스트 부족 / 정책 부재 / 피드백 부재 중 어디에 해당하는가?" | 컴포넌트 유형 결정 |
| **해결 설계** | "이 문제를 반복적으로 방지하려면 어떤 구조를 레포에 추가해야 하는가?" | Phase 3 입력 생성 |

**FitTrack 시나리오 예시** (모듈 1):
> - **행동 관찰**: 에이전트가 `raw_events`에 직접 `SELECT COUNT(DISTINCT user_id)` 쿼리를 실행 — dbt mart 계층을 무시
> - **위험 평가**: 프로덕션에서는 raw 테이블 스키마 변경 시 분석 결과가 깨짐, 비용 증가
> - **원인 분석**: 컨텍스트 부족 — 에이전트가 dbt 모델 계층 구조를 알지 못함
> - **해결 설계**: `AGENTS.md`에 데이터 계약 및 모델 계층 명시 → 스캐폴딩 컴포넌트

---

#### Phase 3: 창작 (Create)

**정의**: Phase 2에서 식별한 문제를 해결하는 **새로운 하니스 컴포넌트**(규칙, 스킬, 훅, 워크플로 정의)를 처음부터 설계·구현하고 검증하는 단계입니다.

**목적**: 에이전트의 행동을 개선하는 실질적인 산출물을 레포지토리에 추가하고, 그 효과를 확인합니다.

| 항목 | 설명 |
|------|------|
| **입력(Input)** | • Phase 2의 문제-컴포넌트 매핑 표<br>• 해당 모듈의 하니스 컴포넌트 명세 (각 모듈 문서에 명시)<br>• Claude Code 스킬/훅 정의 컨벤션 (examples/ 참조) |
| **활동(Activity)** | • 새로운 하니스 컴포넌트를 코드/설정 파일로 구현<br>• 동일한 프롬프트로 에이전트를 재실행하여 행동 변화 확인 (before/after 비교)<br>• 자기 점검 체크리스트로 산출물 품질 검증 |
| **산출물(Output)** | • **하니스 컴포넌트 파일**: 모듈별 산출물 (아래 표 참조)<br>• **행동 변화 기록**: 동일 프롬프트에 대한 에이전트 행동 before/after 비교<br>• **자기 점검 체크리스트**: 모듈별 완료 기준 충족 여부 |

**모듈별 Phase 3 산출물**:

| 모듈 | 하니스 계층 | 주요 산출물 |
|------|-------------|-------------|
| 모듈 1 | 훅·설정 | `.claude/settings.json` (hooks + permissions), `bq-cost-guard.sh`, `dbt-auto-test.sh` |
| 모듈 2 | 슬래시 커맨드 | `.claude/commands/analyze.md`, `check-cost.md`, `validate-models.md`, `generate-report.md` |
| 모듈 3 | 오케스트레이션 | `.github/workflows/auto-analyze.yml`, 7단계 라벨 전환 로직, 에러 처리 훅 |
| 모듈 4 | 통합/개선 | 엔트로피 감지 규칙, `AGENTS.md` 업데이트, 워크플로 개선 기록 |

**FitTrack 시나리오 예시** (모듈 1):
> `.claude/settings.json`에 비용 가드 훅을 등록합니다:
> ```json
> "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "bash .claude/hooks/bq-cost-guard.sh"}]}]
> ```
> 이후 에이전트가 `bq query`를 실행하려 할 때마다 dry-run 비용이 자동으로 확인되며, 1GB 초과 시 차단됩니다.

---

#### Phase 간 전환 기준

각 Phase에서 다음 Phase로 넘어가기 위한 **전환 기준(Transition Criteria)**:

**관찰 → 수정 전환 기준**:

| # | 기준 | 검증 방법 |
|---|------|-----------|
| 1 | 최소 2회의 에이전트 작업 실행 완료 | 프롬프트 이력 및 에이전트 출력 확인 |
| 2 | 각 실행에서 1건 이상의 관찰 사항 기록 | 관찰 노트에 구체적 행동 기술 존재 여부 확인 |
| 3 | 성공과 실패 양쪽 모두 경험 | 관찰 노트에 성공/실패 분류가 모두 존재 |

**수정 → 창작 전환 기준**:

| # | 기준 | 검증 방법 |
|---|------|-----------|
| 1 | 모든 수정 질문에 대한 서면 답변 완료 | 수정 기록 문서에서 빈 항목 없음 확인 |
| 2 | 최소 1건의 문제를 하니스 컴포넌트 유형에 매핑 | 문제-컴포넌트 매핑 표에 1행 이상 존재 |
| 3 | 매핑된 컴포넌트가 해당 모듈의 학습 목표 범위 내 | 매핑 표의 컴포넌트 유형이 모듈 산출물 목록에 포함 |

**창작 → 다음 모듈 전환 기준**:

| # | 기준 | 검증 방법 |
|---|------|-----------|
| 1 | 해당 모듈의 기대 산출물이 모두 레포에 존재 | `ls` / `git status`로 파일 존재 확인 |
| 2 | 동일 프롬프트 재실행 시 에이전트 행동 개선 확인 | before/after 비교 기록에 구체적 차이 명시 |
| 3 | 자기 점검 체크리스트의 모든 항목 통과 | 각 체크리스트 항목의 검증 방법 실행 완료 |

---

#### 사이클 적용 매트릭스

아래 표는 각 모듈에서 3단계 사이클이 어떤 구체적 활동으로 구현되는지를 보여줍니다:

| 모듈 | Phase 1 (관찰) | Phase 2 (수정) | Phase 3 (창작) |
|------|----------------|----------------|----------------|
| **모듈 1** | `AGENTS.md` 없이 DAU 분석 요청 | 에이전트의 컨텍스트 부족 문제 분석 | `AGENTS.md`, 데이터 계약, 이슈 템플릿 작성 |
| **모듈 2** | 스킬/훅 없이 전체 분석 워크플로 실행 | 정책 미준수, 피드백 부재 문제 분석 | 권한 정책, 커스텀 슬래시 명령, pre-commit 훅 구현 |
| **모듈 3** | 수동 트리거로 7단계 워크플로 실행 | 단계 간 전환 실패, 에러 복구 문제 분석 | GitHub Actions 워크플로, 라벨 전환 로직 구현 |
| **모듈 4** | 전체 파이프라인을 처음부터 끝까지 자동 실행 | 하니스 열화(엔트로피), 유지보수 부담 분석 | 엔트로피 감지 규칙, `AGENTS.md` 갱신, 개선 기록 작성 |

---

### 반복 가능성 가이드라인 (Repeatability Guidelines)

위 3단계 학습 사이클은 모듈 1~4에 걸쳐 **동일한 구조를 반복**하되, 각 모듈의 하니스 계층에 맞게 **구체적 활동이 적응(adapt)** 됩니다. 이 섹션은 강사와 수강생이 사이클의 반복 패턴을 명확히 인식하고, 모듈 간 일관성을 유지하면서도 각 모듈 고유의 맥락에 맞게 사이클을 조정하는 방법을 안내합니다.

> **핵심 원칙**: 사이클의 **구조는 고정**하되, **내용은 적응**합니다. Phase 1(관찰)은 항상 "에이전트가 어떻게 동작하는지 지켜보고 기록하기"이고, Phase 2(수정)는 항상 "관찰된 문제를 분석하고 기존 컴포넌트를 수정하기"이며, Phase 3(창작)은 항상 "새로운 컴포넌트를 처음부터 설계·구현하기"입니다. 변하는 것은 관찰 대상, 수정 범위, 창작할 컴포넌트입니다.

#### 크로스 모듈 상세 매핑 테이블

아래 테이블은 3단계 사이클의 각 세부 요소가 모듈별로 어떻게 구체화되는지를 보여줍니다. 각 행은 사이클의 공통 구조 요소이며, 열은 모듈별 적응 결과입니다.

**Phase 1 (관찰) — 모듈별 매핑**:

| 사이클 요소 | 모듈 1: 스캐폴딩 | 모듈 2: 스킬/훅 | 모듈 3: 오케스트레이션 | 모듈 4: 통합/개선 |
|---|---|---|---|---|
| **관찰의 전제 조건** | `AGENTS.md` 미존재 상태 | 스킬/훅 미설정 상태 (`.claude/` 없음) | 워크플로 YAML 미작성, 수동 라벨 전환 | 모듈 1~3의 모든 하니스 컴포넌트 존재 |
| **에이전트에게 부여할 작업** | "FitTrack 1월 DAU를 일별 집계해줘" | "DAU 분석 이슈를 파싱하여 marimo 노트북 생성해줘" | 수동으로 `auto-analyze` 라벨 부착 후 7단계 흐름 관찰 | 새로운 분석 이슈("주간 리텐션율 추이")로 전체 파이프라인 자동 실행 |
| **관찰 초점** | 에이전트가 dbt 모델 계층을 인식하는가? raw 테이블 직접 접근 여부 | 비용 체크 수행 여부, dbt test 실행 여부, 노트북 규약 준수 | 라벨 전환 성공/실패, 단계 간 산출물 전달 정합성 | 기존 패턴 복사로 인한 엔트로피(중복 SQL, 미문서 소스) 발생 여부 |
| **기록할 관찰 문서** | `evidence/module-1-observations.md` | `evidence/module-2-observations.md` | `evidence/module-3-observations.md` | `evidence/module-4-observations.md` |
| **최소 실행 횟수** | 2회 (스캐폴딩 없이 → 있는 상태 비교) | 2회 (스킬/훅 없이 → 있는 상태 비교) | 1회 전체 파이프라인 + 오류 시 1회 재시도 | 2회 (첫 실행 → 개선 후 재실행) |
| **소요 시간 (목표)** | 30~40분 | 40~50분 | 40~60분 (Actions 실행 대기 포함) | 20~30분 |

**Phase 2 (수정) — 모듈별 매핑**:

| 사이클 요소 | 모듈 1: 스캐폴딩 | 모듈 2: 스킬/훅 | 모듈 3: 오케스트레이션 | 모듈 4: 통합/개선 |
|---|---|---|---|---|
| **수정 영역 수** | 3개 영역 (초기화/구조/설정) | 4개 영역 (스킬 설계/훅 효과/증거 스키마/실무 적용) | 4개 영역 (워크플로 설계/CI·CD 통합/엔드투엔드 조율/실무 적용) | 2개 영역 (코스 전체 수정/실무 적용 계획) |
| **수정 질문 총 수** | 6개 | 8개 | 8개+ | 3개 |
| **핵심 분석 관점** | "에이전트에게 컨텍스트가 부족했던 지점은?" | "정책이 없어서 발생한 위반과 피드백이 없어서 놓친 오류는?" | "자동화 실패 지점과 단계 간 정보 손실 지점은?" | "하니스 전체의 ROI와 유지보수 부담은?" |
| **문제 → 컴포넌트 매핑 대상** | 규칙/문서 → `AGENTS.md` 섹션, `sources.yml` description | 스킬 정의, 훅 설정, 완료 증거 스키마 | 워크플로 YAML 분기, 프롬프트 보강, 오류 처리 로직 | 엔트로피 감지 규칙, 작업 분류표, `AGENTS.md` 갱신 |
| **수정 기록 문서** | `evidence/module-1-retrospective.md` | `evidence/module-2-retrospective.md` | `evidence/module-3-retrospective.md` | `evidence/module-4-retrospective.md` |
| **다음 모듈 연결** | 훅 후보 목록 → 모듈 2 입력 | 종합 템플릿의 "모듈 3 진입 준비도" 확인 | 종합 템플릿의 "모듈 4 진입 전 확인" 항목 | — (코스 종료, 실무 적용 계획 수립) |
| **소요 시간 (목표)** | 20~25분 | 25~30분 | 25~30분 | 15~20분 |

**Phase 3 (창작) — 모듈별 매핑**:

| 사이클 요소 | 모듈 1: 스캐폴딩 | 모듈 2: 스킬/훅 | 모듈 3: 오케스트레이션 | 모듈 4: 통합/개선 |
|---|---|---|---|---|
| **하니스 계층** | 스캐폴딩 | 스킬/훅 | 오케스트레이션 | 통합 (전 계층 횡단) |
| **주요 산출물** | `AGENTS.md`, `sources.yml` 보강, Issue 템플릿 | `.claude/settings.json`, 4개 커스텀 슬래시 명령, pre-commit 훅 | `.github/workflows/auto-analyze.yml`, 라벨 전환 로직, 에러 처리 | 엔트로피 감지 규칙, `AGENTS.md` v2, 워크플로 개선 기록 |
| **코드 vs 설정 비율** | 설정(문서) 90% / 코드 10% | 코드 60% / 설정 40% | 코드 80% / 설정 20% | 문서 60% / 코드 30% / 설정 10% |
| **before/after 비교 기준** | 에이전트가 dbt 모델 계층을 따르는가? | 비용 체크/dbt test가 자동 실행되는가? | 7단계가 자동으로 연쇄 실행되는가? | 재실행 시 이전보다 산출물 품질이 높은가? |
| **검증 방법** | 동일 프롬프트 재실행 후 에이전트 행동 비교 | 의도적 위반 테스트 (실패하는 모델 커밋 시도) | 이슈에 라벨 부착 후 `done`까지 자동 완료 확인 | 두 번째 실행의 오류 수/워크플로 시간 감소 확인 |
| **소요 시간 (목표)** | 30~40분 | 50~60분 | 50~70분 | 20~30분 |

#### 모듈별 적응 노트 (Adaptation Notes)

각 모듈은 동일한 3단계 사이클을 적용하지만, 하니스 계층의 특성에 따라 사이클의 실행 방식이 달라집니다. 아래는 각 모듈에서 강사와 수강생이 유의해야 할 **적응 포인트**입니다.

**모듈 1 (스캐폴딩) — "문서의 힘을 체감하기"**

| 적응 포인트 | 설명 |
|---|---|
| **관찰 단계의 특수성** | 코스 첫 사이클이므로, 수강생은 "에이전트에게 의도적으로 하니스 없이 작업시키기"에 어색할 수 있음. "지금은 일부러 가이드 없이 시켜보는 것"임을 명확히 안내 |
| **수정 단계의 초점** | 수정이 "코드 품질"이 아니라 **"에이전트가 추측해야 했던 정보"**에 집중해야 함. 에이전트의 코드가 기술적으로 정확하더라도, 추측에 기반한 것이라면 문제로 기록 |
| **창작 단계의 난이도** | 산출물이 코드가 아닌 **문서/설정** 위주(AGENTS.md, sources.yml, Issue 템플릿)이므로, "코드를 작성하지 않았는데 하니스를 만든 것인가?"라는 의문이 생길 수 있음. 문서도 에이전트의 행동을 제약하는 유효한 하니스 컴포넌트임을 강조 |
| **다음 모듈과의 연결** | 수정 단계에서 작성한 "훅 후보 목록"(`evidence/hook-candidates.md`)이 모듈 2의 창작 단계 입력이 됨. 이 목록이 구체적일수록 모듈 2가 수월해지므로, 수정 단계에서 충분히 시간 투자 권장 |

**모듈 2 (스킬/훅) — "자동 검증의 가치 확인하기"**

| 적응 포인트 | 설명 |
|---|---|
| **관찰 단계의 특수성** | 모듈 1의 스캐폴딩이 있는 상태에서 시작하므로, 에이전트가 이미 일부 규칙을 따름. 관찰할 것은 "규칙은 알지만 검증 없이 위반하는 경우"임 |
| **수정 단계의 초점** | 수정 영역이 4개로 늘어남 — 시간이 부족하면 "스킬 설계"와 "훅 효과" 영역을 우선 진행하고, 나머지는 자습 과제로 전환 가능 |
| **창작 단계의 난이도** | 이 모듈의 Phase 3이 **코드 비중이 가장 높음** (스킬 정의 4개 + 훅 설정 + 완료 증거 스키마). 시간 압박 시 `/analyze`와 `/check-cost` 2개 스킬만 필수로 구현하고, 나머지는 선택 과제로 조정 |
| **다음 모듈과의 연결** | 회고 종합 템플릿의 "모듈 3 진입 준비도" 3항목(스킬 동작 확인, 훅 동작 확인, 증거 파일 생성 확인)을 모두 충족해야 모듈 3으로 진행. 미충족 시 해당 항목만 보완 후 진행 |

**모듈 3 (오케스트레이션) — "자동화의 복잡성 직면하기"**

| 적응 포인트 | 설명 |
|---|---|
| **관찰 단계의 특수성** | 다른 모듈과 달리 Phase 1에서 **GitHub Actions 실행 대기 시간**이 존재 (단계 간 전환에 30초~1분). 대기 시간 동안 회고 질문을 미리 읽어두면 시간 효율적 |
| **수정 단계의 초점** | 오류 처리가 핵심 회고 영역. 실제 파이프라인 실행 중 발생한 오류(또는 의도적으로 발생시킨 오류)를 기반으로 오류 분류 체계(INFRA/DATA/AGENT/WORKFLOW)의 유효성을 검토 |
| **창작 단계의 난이도** | 이 모듈의 Phase 3이 **가장 난이도가 높음** — YAML 문법, GitHub API, Claude Agent SDK를 동시에 다룸. `actionlint`로 YAML 유효성을 먼저 확인한 후 단계별로 진행 권장 |
| **다음 모듈과의 연결** | 종합 템플릿의 "모듈 4 진입 전 확인" 3항목(7단계 완주, 오류 처리 1회 이상 검증, PR 자동 생성)이 게이트. 7단계 완주가 안 되면 실패 단계만 격리하여 디버깅 후 재시도 |

**모듈 4 (통합/개선) — "전체를 조망하고 실무에 연결하기"**

| 적응 포인트 | 설명 |
|---|---|
| **관찰 단계의 특수성** | 이전 모듈과 달리 "하니스 부재" 상태가 아닌 "하니스 완성" 상태에서 시작. Phase 1의 목적은 "하니스가 잘 작동하는가?"가 아니라 **"하니스가 시간이 지나면서 어떻게 열화하는가?"**를 관찰하는 것 |
| **수정 단계의 초점** | 수정 범위가 **코스 전체**로 확대됨. 개별 모듈이 아니라 세 계층(스캐폴딩/스킬·훅/오케스트레이션)의 상호작용과 유지보수 부담을 종합적으로 평가 |
| **창작 단계의 난이도** | 새로운 컴포넌트를 만드는 것이 아니라 **기존 컴포넌트를 개선**하는 것이므로, "무엇을 만들어야 하는지"보다 "무엇을 고쳐야 하는지"를 판단하는 역량이 필요. Git 이력 분석(`git log`, `git diff`)을 적극 활용 |
| **실무 연결** | 이 모듈의 Phase 3 산출물에 **실무 적용 계획**이 포함됨. 수강생이 본인의 실제 프로젝트에 하니스를 적용할 때 어떤 모듈부터 시작할지, 우선순위를 정하는 것이 핵심 |

#### 사이클 실행 시간 배분 가이드

모듈별로 3단계 사이클의 시간 배분 비율은 다릅니다. 아래 가이드를 참고하되, 수강생의 속도에 따라 조정하세요.

| 모듈 | 총 시간 | Phase 1 (관찰) | Phase 2 (수정) | Phase 3 (창작) | 비율 |
|---|---|---|---|---|---|
| **모듈 1** | 1.5~2h | 30~40분 | 20~25분 | 30~40분 | 35% / 25% / 40% |
| **모듈 2** | 2~3h | 40~50분 | 25~30분 | 50~60분 | 35% / 20% / 45% |
| **모듈 3** | 2~3h | 40~60분 | 25~30분 | 50~70분 | 30% / 20% / 50% |
| **모듈 4** | 1~1.5h | 20~30분 | 15~20분 | 20~30분 | 35% / 25% / 40% |

> **패턴**: 모듈이 진행될수록 Phase 3(창작)의 비중이 증가합니다 — 이전 모듈에서 축적된 관찰과 수정 경험이 창작 속도를 높이는 대신, 창작할 컴포넌트의 복잡도가 높아지기 때문입니다. 모듈 4에서 비율이 다시 균등해지는 것은, 기존 컴포넌트 "개선"이 신규 "창작"보다 단위 시간이 짧기 때문입니다.

#### 사이클 반복의 누적 효과

3단계 사이클을 4개 모듈에 걸쳐 반복하면서, 수강생은 다음과 같은 **누적 효과**를 경험합니다:

```
모듈 1 사이클 완료 후:
  ├── 에이전트가 레포를 "읽을 수" 있음 (스캐폴딩)
  └── 관찰 기반 문제 식별 역량 습득

모듈 2 사이클 완료 후:
  ├── 에이전트가 "안전하게" 작업할 수 있음 (스킬/훅)
  ├── 하니스 컴포넌트 구현 역량 습득
  └── 수정 단계 속도 향상 — 수정 패턴에 익숙해짐

모듈 3 사이클 완료 후:
  ├── 에이전트가 "자율적으로" 분석 수행 가능 (오케스트레이션)
  ├── 복잡한 시스템의 오류 진단 역량 습득
  └── 관찰 단계 정밀도 향상 — 무엇을 관찰해야 하는지 앎

모듈 4 사이클 완료 후:
  ├── 하니스 전체를 유지보수할 수 있음 (통합)
  ├── 사이클 자체를 실무에 독립적으로 적용할 수 있는 메타 역량 습득
  └── 에이전트 협업의 장기적 전략 수립 가능
```

> **강사 팁**: 모듈 4의 수정 단계에서 "모듈 1의 사이클과 모듈 3의 사이클에서 수정 단계의 품질 차이를 느꼈나요?"라고 질문하세요. 대부분의 수강생이 "후반부에서 관찰이 더 구체적이고 수정이 더 정확해졌다"고 답하며, 이것 자체가 관찰-수정-창작 사이클 반복의 학습 효과를 증명합니다.

---

## 샘플 프로젝트 상세: 모바일 앱 DAU/MAU 분석

### 시나리오

B2C 모바일 앱 "FitTrack" (가상 피트니스 앱)의 사용자 활동 데이터를 분석합니다.

### 합성 데이터 구조

합성 데이터는 B2C 피트니스 앱 "FitTrack"의 3개월치(2026-01-01 ~ 2026-03-31) 사용자 활동 데이터를 시뮬레이션합니다. BigQuery 데이터셋(`fittrack_raw`)에 3개의 원시 테이블로 적재됩니다.

#### 테이블 개요

| 테이블 | 설명 | 예상 행 수 | 그레인(grain) |
|--------|------|------------|---------------|
| `raw_events` | 앱 내 개별 사용자 행동 이벤트 | ~500,000 | 이벤트 1건 = 1행 |
| `raw_users` | 사용자 프로필 및 가입 정보 | ~10,000 | 사용자 1명 = 1행 |
| `raw_sessions` | 앱 세션(접속) 기록 | ~150,000 | 세션 1건 = 1행 |

#### `raw_events` — 앱 이벤트 로그

사용자가 앱 내에서 수행하는 모든 행동을 기록합니다. DAU 산출의 기본 소스이며, 이벤트 유형별 분석에 활용됩니다.

| 컬럼명 | 데이터 타입 | NULL 허용 | 설명 |
|--------|-------------|-----------|------|
| `event_id` | `STRING` | NOT NULL | 이벤트 고유 식별자 (UUID v4) |
| `user_id` | `STRING` | NOT NULL | 사용자 고유 식별자, `raw_users.user_id` 참조 |
| `session_id` | `STRING` | NOT NULL | 세션 식별자, `raw_sessions.session_id` 참조 |
| `event_type` | `STRING` | NOT NULL | 이벤트 유형 (아래 허용 값 참조) |
| `event_timestamp` | `TIMESTAMP` | NOT NULL | 이벤트 발생 시각 (UTC) |
| `event_date` | `DATE` | NOT NULL | 이벤트 발생 일자 (UTC 기준, 파티션 키) |
| `platform` | `STRING` | NOT NULL | 클라이언트 플랫폼: `ios`, `android` |
| `app_version` | `STRING` | NOT NULL | 앱 버전 (semver 형식, 예: `3.2.1`) |
| `device_model` | `STRING` | NULL 허용 | 기기 모델명 (예: `iPhone 15`, `Galaxy S24`) |
| `event_properties` | `JSON` | NULL 허용 | 이벤트별 추가 속성 (JSON 문자열) |

**`event_type` 허용 값:**

| 값 | 설명 |
|----|------|
| `app_open` | 앱 실행 (포그라운드 진입) |
| `app_close` | 앱 종료 (백그라운드 이동) |
| `screen_view` | 화면 조회 |
| `workout_start` | 운동 시작 |
| `workout_complete` | 운동 완료 |
| `goal_set` | 목표 설정 |
| `goal_achieved` | 목표 달성 |
| `social_share` | 소셜 공유 |
| `purchase` | 인앱 구매 |
| `push_notification_open` | 푸시 알림 열기 |

**파티션 및 클러스터링:**
- 파티션 키: `event_date` (일별 파티션, 쿼리 비용 최적화)
- 클러스터링 키: `user_id`, `event_type`

#### `raw_users` — 사용자 프로필

앱에 가입한 사용자의 프로필 정보를 저장합니다. 사용자 세그먼트(국가, 구독 등급)별 분석 및 코호트 분석의 기본 디멘전 테이블로 활용됩니다.

| 컬럼명 | 데이터 타입 | NULL 허용 | 설명 |
|--------|-------------|-----------|------|
| `user_id` | `STRING` | NOT NULL | 사용자 고유 식별자 (UUID v4), PK |
| `signup_timestamp` | `TIMESTAMP` | NOT NULL | 가입 시각 (UTC) |
| `signup_date` | `DATE` | NOT NULL | 가입 일자 (UTC 기준) |
| `country` | `STRING` | NOT NULL | 국가 코드 (ISO 3166-1 alpha-2, 예: `KR`, `US`, `JP`) |
| `language` | `STRING` | NOT NULL | 앱 설정 언어 (예: `ko`, `en`, `ja`) |
| `platform` | `STRING` | NOT NULL | 최초 가입 플랫폼: `ios`, `android` |
| `device_type` | `STRING` | NOT NULL | 디바이스 유형: `smartphone`, `tablet` |
| `initial_app_version` | `STRING` | NOT NULL | 가입 시점 앱 버전 (semver 형식, 예: `3.2.1`) |
| `subscription_tier` | `STRING` | NOT NULL | 구독 등급: `free`, `premium`, `premium_plus` |
| `age_group` | `STRING` | NULL 허용 | 연령대: `18-24`, `25-34`, `35-44`, `45-54`, `55+` |
| `referral_source` | `STRING` | NULL 허용 | 유입 채널: `organic`, `paid_search`, `social`, `referral` |
| `is_active` | `BOOLEAN` | NOT NULL | 계정 활성 상태 (탈퇴 시 `false`) |
| `last_active_date` | `DATE` | NULL 허용 | 마지막 활동 일자 (스냅샷 기준) |

**데이터 특성:**
- 전체 ~10,000 사용자 중 약 70%가 활성 상태 (`is_active = true`)
- 국가 분포: KR 40%, US 25%, JP 15%, 기타 20%
- 구독 분포: free 60%, premium 30%, premium_plus 10%
- 디바이스 유형: iOS smartphone 85%/tablet 15%, Android smartphone 92%/tablet 8%
- 가입 시점 앱 버전: 초기 가입자는 이전 버전(3.0.x~3.1.x), 최근 가입자는 최신 버전(3.2.x)에 집중
- 가입일 범위: 2025-01-01 ~ 2026-03-31 (1년 이상의 코호트 분석 가능)

#### `raw_sessions` — 앱 세션 기록

사용자의 앱 접속 단위(세션)를 기록합니다. 세션 기반 DAU 검증, 세션 길이 분석, 일일 세션 빈도 등의 분석에 활용됩니다.

| 컬럼명 | 데이터 타입 | NULL 허용 | 설명 |
|--------|-------------|-----------|------|
| `session_id` | `STRING` | NOT NULL | 세션 고유 식별자 (UUID v4), PK |
| `user_id` | `STRING` | NOT NULL | 사용자 식별자, `raw_users.user_id` 참조 |
| `session_start` | `TIMESTAMP` | NOT NULL | 세션 시작 시각 (UTC) |
| `session_end` | `TIMESTAMP` | NULL 허용 | 세션 종료 시각 (UTC), 비정상 종료 시 NULL |
| `session_date` | `DATE` | NOT NULL | 세션 시작 일자 (UTC 기준, 파티션 키) |
| `session_duration_seconds` | `INT64` | NULL 허용 | 세션 지속 시간 (초), `session_end`가 NULL이면 NULL |
| `platform` | `STRING` | NOT NULL | 플랫폼: `ios`, `android` |
| `app_version` | `STRING` | NOT NULL | 세션 시작 시점의 앱 버전 |
| `device_model` | `STRING` | NULL 허용 | 기기 모델명 |
| `os_version` | `STRING` | NULL 허용 | OS 버전 (예: `iOS 18.2`, `Android 15`) |
| `ip_country` | `STRING` | NULL 허용 | IP 기반 접속 국가 (ISO 3166-1 alpha-2) |
| `event_count` | `INT64` | NOT NULL | 해당 세션 내 발생한 이벤트 수 |
| `screen_count` | `INT64` | NOT NULL | 해당 세션 내 `screen_view` 이벤트 수 (이벤트 생성 후 역산) |

**파티션 및 클러스터링:**
- 파티션 키: `session_date` (일별 파티션)
- 클러스터링 키: `user_id`

**데이터 특성:**
- 평균 세션 길이: ~8분 (480초)
- 사용자당 일평균 세션 수: ~1.7회
- 비정상 종료(`session_end` IS NULL) 비율: ~3%
- `screen_count`: 이벤트 테이블의 `screen_view` 이벤트를 세션별로 집계한 파생 컬럼 (세션 깊이 분석용)

#### 테이블 간 관계

```
raw_users (1) ──── (N) raw_sessions (1) ──── (N) raw_events
   user_id              session_id, user_id         session_id, user_id
```

- `raw_users.user_id` → `raw_sessions.user_id`: 1:N (한 사용자가 여러 세션 생성)
- `raw_sessions.session_id` → `raw_events.session_id`: 1:N (한 세션 내 여러 이벤트 발생)
- `raw_users.user_id` → `raw_events.user_id`: 1:N (비정규화된 참조, 조인 편의용)

#### 합성 데이터 생성 규칙

합성 데이터 생성 스크립트(`scripts/generate_synthetic_data.py`)는 다음 규칙을 따릅니다:

1. **시간 분포**: 활동이 특정 시간대(한국 기준 오전 7-9시, 오후 6-10시)에 집중되도록 가중치 부여
2. **주말 효과**: 주말 DAU가 평일 대비 약 15-20% 증가
3. **이벤트 현실성**: `workout_start` → `workout_complete` 순서 보장, 완료율 약 85%
4. **이탈 시뮬레이션**: 가입 후 시간이 지남에 따라 활동 빈도가 점진적으로 감소하는 패턴 포함
5. **플랫폼 비율**: iOS 55%, Android 45% (한국 시장 반영)
6. **버전 분포**: 최신 3개 버전에 사용자의 90%가 분포

### dbt 모델 구조 (스타터 레포에 포함)

```
models/
├── staging/
│   ├── stg_events.sql          -- 이벤트 클렌징, 타임존 통일
│   ├── stg_users.sql           -- 사용자 프로필 정규화
│   ├── stg_sessions.sql        -- 세션 데이터 정리, 비정상 종료 처리
│   └── sources.yml             -- 소스 테이블 정의 (raw_events, raw_users, raw_sessions)
├── marts/
│   ├── fct_daily_active_users.sql   -- DAU 집계
│   ├── fct_monthly_active_users.sql -- MAU 집계
│   └── fct_retention_cohort.sql     -- 코호트 리텐션 (보너스)
└── schema.yml                  -- 모델 문서화 및 테스트 정의
```

### 분석 이슈 예시

> **제목**: 2026년 1분기 DAU/MAU 트렌드 분석
>
> **문제 정의**: FitTrack 앱의 2026년 1분기 DAU와 MAU 추이를 파악하고, DAU/MAU 비율(stickiness)의 변화를 플랫폼(iOS/Android)별로 비교하라.
>
> **기대 산출물**:
> - 일별 DAU 추이 차트
> - 월별 MAU 추이 차트
> - DAU/MAU 비율 트렌드 (플랫폼별)
> - 주요 발견 요약 (3~5문장)
>
> **데이터 범위**: 2026-01-01 ~ 2026-03-31
> **세그먼트**: platform (iOS, Android)

---

## 평가 기준

이 코스에는 별도 시험이나 캡스톤 프로젝트가 없습니다. 대신, 각 모듈의 **자기 점검 체크리스트**를 통해 학습 목표 달성 여부를 스스로 확인합니다.

### 체크리스트 설계 원칙

모든 체크리스트 항목은 다음 세 요소를 포함합니다:

1. **확인 질문**: "~하는가?" 형태의 구체적 질문
2. **검증 방법**: 터미널 명령, UI 확인, 파일 존재 여부 등 구체적 확인 행동
3. **성공 기준**: 예상되는 정상 결과 (출력 메시지, 파일 경로 등)

---

## 교수자/운영자 참고사항

### 산출물 목록

이 코스 스펙을 기반으로 다음 산출물이 제작됩니다:

| 산출물 | 경로 | 설명 |
|--------|------|------|
| 코스 스펙 (본 문서) | `course-spec.md` | 전체 코스 개요 및 구조 |
| 모듈 가이드 | `modules/module-{0,1,2,3,4}.md` | 모듈별 상세 학습 가이드 |
| 코드 예제 | `examples/` | 스킬, 훅, 워크플로 YAML, AGENTS.md 예제 |
| 교수자 설정 가이드 | `instructor-setup-guide.md` | GCP, GitHub 조직 수준 설정 매뉴얼 |
| 스타터 레포 | (별도 레포) | dbt 프로젝트, 합성 데이터, setup.sh |

### 로컬 도구 설정 vs. 조직 수준 설정

| 구분 | 설정 방식 | 예시 |
|------|-----------|------|
| 로컬 도구 | `setup.sh` 스크립트로 자동화 | uv, dbt, marimo, Claude Code CLI 설치 |
| 조직 수준 | `instructor-setup-guide.md`에 수동 절차 문서화 | GCP 프로젝트 생성, 서비스 계정 발급, GitHub Secret 등록, BigQuery 데이터셋 권한 |

---

## 용어 정리

| 영어 | 한국어 표기 | 설명 |
|------|-------------|------|
| Harness Engineering | 하니스 엔지니어링 | 에이전트가 안정적으로 작업할 수 있도록 환경을 설계하는 엔지니어링 |
| Scaffolding | 스캐폴딩 | 레포 구조, 패키지 관리, 기본 설정 등 기반 환경 |
| Skill | 스킬 | Claude Code에서 호출 가능한 재사용 작업 단위 |
| Hook | 훅 | 특정 이벤트에 자동 실행되는 검증/정책 로직 |
| Orchestration | 오케스트레이션 | 이슈 기반 자동 워크플로 제어 루프 |
| Legibility | 가독성 | 에이전트가 레포를 이해할 수 있는 정도 |
| Proof of Completion | 완료 증거 | 작업 완료를 기계적으로 확인할 수 있는 아티팩트 |
| Data Contract | 데이터 계약 | 테이블의 소유자, 그레인, 스키마, 신선도 기대치 선언 |
| Entropy | 엔트로피 | 에이전트가 나쁜 패턴을 복사하면서 발생하는 품질 저하 |
| DAU | DAU (일간 활성 사용자) | Daily Active Users |
| MAU | MAU (월간 활성 사용자) | Monthly Active Users |
| Stickiness | 스티키니스 | DAU/MAU 비율, 앱 사용 빈도 지표 |

---

## 참고 자료

- OpenAI, "Harness engineering: leveraging Codex in an agent-first world" (2026.02.11)
- `openai/symphony` 레포지토리 및 SPEC.md
- Anthropic Claude Code 공식 문서
- dbt 공식 문서 (dbt Core + MetricFlow)
- marimo 공식 문서
- GitHub Actions 공식 문서
