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

- `setup.sh`를 실행하여 Claude Code CLI, uv, dbt가 포함된 로컬 개발 환경을 **설정할 수 있다** — 세 도구 모두 버전 번호가 출력되는 것을 터미널에서 확인 *(검증: `claude --version && uv --version && dbt --version` 출력. marimo는 이후 모듈에서 도입)*
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


### 실습 단계

모듈 0의 실습(레포 클론, 로컬 환경 설정, GCP 서비스 계정·GitHub Secret 등록, 합성 데이터 생성·적재, dbt 빌드·검증, 레포 이해도 기준선 측정)은 별도 실습 문서에서 단계별로 안내합니다:

- 환경/인프라 설정 절차: [`instructor-setup-guide.md`](instructor-setup-guide.md)
- 학습자 실습 가이드: [`module-0-project-setup/README.md`](module-0-project-setup/README.md)

> 이 스펙은 각 모듈의 **학습 목표·핵심 개념·자기 점검 기준**을 정의합니다. 실제 빌드 단계(명령어, 파일 작성)는 위 실습 문서를 따르세요.

#### 핵심 개념 정리 — 도구별 모듈 역할

| 도구 | 모듈 0 | 모듈 1 | 모듈 2 | 모듈 3 | 모듈 4 |
|------|--------|--------|--------|--------|--------|
| `.claude/settings.json` | — | 훅·permissions 기초 | 커맨드에서 참조 | permissions.allow/deny 완성 | CI 환경 복제 |
| dbt | 환경 검증 | 훅으로 자동 컴파일 | 커맨드에서 run/test | 권한 내에서 실행 | 자동 실행 (파이프라인) |
| marimo | — (이후 모듈에서 도입) | — | 리포트 커맨드 | — | 자동 생성 (stage:6~7) |
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
| 1 | 로컬 개발 환경 | 터미널에서 claude, uv, dbt 실행 가능 (marimo는 이후 모듈에서 도입) | 하니스 인프라 |
| 2 | BigQuery 합성 데이터 | `raw_events`(~50만 건), `raw_users`(~1만 명), `raw_sessions` 테이블 | 파이프라인 입력 |
| 3 | dbt 빌드·테스트 결과 | staging + mart 모델 6개 전체 빌드 성공, 테스트 0 Fail | 파이프라인 산출물 |
| 4 | GitHub Secrets | `GCP_SA_KEY`, `GCP_PROJECT_ID`, `CLAUDE_TOKEN`, 인증 토큰 | 하니스 설정 |
| 5 | Claude Code 기준선 응답 | 직접 기록 (텍스트) — `evidence/module-0-baseline.md` | 하니스 효과 측정용 |

### 자가 점검

**[점검 1/6] 도구 설치 확인**

- [ ] `claude --version` 실행 시 버전 번호가 출력되는가?
  - **검증 명령**: 터미널에서 `claude --version && uv --version && dbt --version` 실행 (marimo는 이후 모듈에서 도입)
  - **✅ 합격 기준**: 세 도구 모두 버전 번호 출력 (예: `claude 1.x.x`, `uv 0.x.x`)
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

> **모듈 진행 조건**: 위 6개 항목 **전부 ✅ 합격** 후 모듈 1(`module-1-hooks/`)로 진행하세요.
> 상세 실습 가이드: [`module-0-project-setup/README.md`](module-0-project-setup/README.md) 및 [`instructor-setup-guide.md`](instructor-setup-guide.md) 참조

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


### 실습 단계

이 모듈의 단계별 실습(명령어·파일 작성)과 **참조 구현 전체 소스**(훅 스크립트, `settings.json`, 슬래시 커맨드 본문, 권한 정책, GitHub Actions 워크플로)는 [`build-guide.md`](build-guide.md)의 "모듈 1" 섹션을 참조하세요. 학습자용 단계별 가이드는 [`module-1-hooks/README.md`](module-1-hooks/) 에도 포함되어 있습니다.


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
> 상세 실습 가이드: [`build-guide.md`](build-guide.md)의 모듈 1 섹션 및 [`module-1-hooks/README.md`](module-1-hooks/README.md) 참조

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


### 실습 단계

이 모듈의 단계별 실습(명령어·파일 작성)과 **참조 구현 전체 소스**(훅 스크립트, `settings.json`, 슬래시 커맨드 본문, 권한 정책, GitHub Actions 워크플로)는 [`build-guide.md`](build-guide.md)의 "모듈 2" 섹션을 참조하세요. 학습자용 단계별 가이드는 [`module-2-slash-commands/README.md`](module-2-slash-commands/) 에도 포함되어 있습니다.


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
> 상세 실습 가이드: [`build-guide.md`](build-guide.md)의 모듈 2 섹션 및 [`module-2-slash-commands/README.md`](module-2-slash-commands/README.md) 참조

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


### 실습 단계

이 모듈의 단계별 실습(명령어·파일 작성)과 **참조 구현 전체 소스**(훅 스크립트, `settings.json`, 슬래시 커맨드 본문, 권한 정책, GitHub Actions 워크플로)는 [`build-guide.md`](build-guide.md)의 "모듈 3" 섹션을 참조하세요. 학습자용 단계별 가이드는 [`module-3-orchestration/README.md`](module-3-orchestration/) 에도 포함되어 있습니다.

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

> **모듈 진행 조건**: 위 5개 항목 **전부 ✅ 합격** 후 모듈 4(`module-4-error-handling/`)로 진행하세요.
> 상세 실습 가이드: [`build-guide.md`](build-guide.md)의 모듈 3 섹션 및 [`module-3-orchestration/README.md`](module-3-orchestration/README.md) 참조

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


### 실습 단계

이 모듈의 단계별 실습(명령어·파일 작성)과 **참조 구현 전체 소스**(훅 스크립트, `settings.json`, 슬래시 커맨드 본문, 권한 정책, GitHub Actions 워크플로)는 [`build-guide.md`](build-guide.md)의 "모듈 4" 섹션을 참조하세요. 학습자용 단계별 가이드는 [`module-4-error-handling/README.md`](module-4-error-handling/) 에도 포함되어 있습니다.


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
> 상세 실습 가이드: [`build-guide.md`](build-guide.md)의 모듈 4 섹션 및 [`module-4-error-handling/README.md`](module-4-error-handling/README.md) 참조

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


### 3단계 학습 사이클: 관찰-수정-창작

각 모듈(1~4)은 **관찰(observe) → 수정(modify) → 창작(create)** 사이클을 반복합니다. 에이전트의 행동을 먼저 관찰하고, 기존 하니스 컴포넌트를 수정하며 원인을 파악한 뒤, 재발 방지를 위한 새 컴포넌트를 창작합니다.

| Phase | 핵심 활동 | 모듈별 산출물(요약) |
|-------|-----------|--------------------|
| 관찰(observe) | 에이전트 행동을 실행·기록 | 관찰 노트 (`evidence/module-N-observations.md`) |
| 수정(modify) | 문제를 분류하고 기존 컴포넌트 조정 | 회고 (`evidence/module-N-retrospective.md`) |
| 창작(create) | 새 하니스 컴포넌트 설계·구현·검증 | 모듈별 하니스 산출물 |

> 사이클의 교육적 근거, Phase별 상세 구조, 크로스 모듈 매핑·시간 배분 가이드는 [`references/learning-cycle-framework.md`](references/learning-cycle-framework.md)에 정리되어 있습니다.


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
| 빌드 가이드 | `build-guide.md` | 모듈 1~4 단계별 실습 및 참조 구현 소스 |
| 모듈 프로젝트 | `module-{0,1,2,3,4}-*/` | 모듈별 독립 실행 프로젝트 (README, 하니스 산출 파일 포함) |
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
