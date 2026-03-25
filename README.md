# 하니스 엔지니어링 for 데이터 분석

> Claude Code와 GitHub Actions를 활용한 에이전트 기반 데이터 분석 자동화 코스

**샘플 프로젝트**: B2C 모바일 앱(FitTrack)의 DAU/MAU 분석
**기술 스택**: Claude Code · BigQuery · dbt · marimo · GitHub Actions

---

## 코스 소개

이 코스는 **하니스 엔지니어링(harness engineering)** 개념을 데이터 분석 워크플로에 적용하는 방법을 실습 중심으로 다룹니다.

- **스캐폴딩**: 에이전트가 작동하는 레포지토리 구조 설계
- **훅(Hook)**: 에이전트 정책을 코드로 구현
- **슬래시 커맨드**: 재사용 가능한 에이전트 작업 명세화
- **오케스트레이션**: 권한 정책으로 에이전트 경계 설계
- **종단간 통합**: GitHub Actions CI/CD 파이프라인과 오류 처리

각 모듈은 **독립적인 완성형 프로젝트**로, 이전 모듈 없이도 시작할 수 있습니다.

---

## 모듈 구성

| 모듈 | 디렉터리 | 주제 | 학습 시간 |
|------|----------|------|-----------|
| 0 | [`module-0-project-setup/`](module-0-project-setup/) | 환경 설정 및 프로젝트 이해 | 2~3시간 |
| 1 | [`module-1-hooks/`](module-1-hooks/) | 훅과 설정 엔지니어링 | 1.5~2시간 |
| 2 | [`module-2-slash-commands/`](module-2-slash-commands/) | 슬래시 커맨드 작성 | 1.5~2시간 |
| 3 | [`module-3-orchestration/`](module-3-orchestration/) | 권한 오케스트레이션 | 1.5~2시간 |
| 4 | [`module-4-error-handling/`](module-4-error-handling/) | 종단간 통합 및 오류 처리 | 2.5~3.5시간 |

### 모듈 선택 가이드

- **처음 시작하는 경우** → [`module-0-project-setup/`](module-0-project-setup/)부터 순서대로 진행
- **환경이 이미 설정된 경우** → [`module-1-hooks/`](module-1-hooks/)부터 시작 가능 (Module 0 스냅샷 포함)
- **훅/커맨드 실습만 필요한 경우** → [`module-1-hooks/`](module-1-hooks/) 또는 [`module-2-slash-commands/`](module-2-slash-commands/) 독립 실행
- **권한 설계에 집중하려는 경우** → [`module-3-orchestration/`](module-3-orchestration/) 독립 실행
- **전체 워크플로 통합 실습** → [`module-4-error-handling/`](module-4-error-handling/) 독립 실행

---

## 빠른 시작

```bash
# 원하는 모듈 디렉터리로 이동
cd module-0-project-setup   # 또는 원하는 모듈

# .env 파일 설정
cp .env.example .env
# .env 파일을 편집하여 GCP 프로젝트 ID 등 환경변수 입력

# 의존성 설치
uv sync

# Claude Code로 시작
claude .
```

각 모듈의 `README.md`에 상세한 시작 가이드가 포함되어 있습니다.

---

## 사전 요구사항

| 영역 | 요구 수준 |
|------|-----------|
| SQL | 중급 이상 (집계, 조인, 서브쿼리) |
| dbt | 기본 (모델, 테스트, 소스 정의 경험) |
| Python | 기본 (스크립트 실행, 패키지 관리) |
| Git/GitHub | 기본 (커밋, 브랜치, PR) |
| BigQuery | 기초 (쿼리 실행 경험) |
| Claude Code | 불필요 — 코스에서 처음부터 학습 |

### 필수 도구

- `uv` — Python 패키지 매니저
- `claude` — Claude Code CLI
- `gcloud` — Google Cloud SDK
- `gh` — GitHub CLI

---

## 레포지토리 구조

```
data-analysis-with-claude/
├── README.md                          ← 코스 랜딩 페이지 (이 파일)
├── CLAUDE.md                          ← 레포 전체 Claude Code 에이전트 지침
├── pyproject.toml                     ← 레포 전체 개발 도구 설정
│
├── module-0-project-setup/            ← 모듈 0: 환경 설정 및 프로젝트 이해
├── module-1-hooks/                    ← 모듈 1: 훅과 설정 엔지니어링
├── module-2-slash-commands/           ← 모듈 2: 슬래시 커맨드 작성
├── module-3-orchestration/            ← 모듈 3: 권한 오케스트레이션
├── module-4-error-handling/           ← 모듈 4: 종단간 통합 및 오류 처리
│
└── initialize/                        ← 코스 관리 (강사용)
    ├── README.md                      ← 코스 개요 및 강사 가이드
    ├── course-spec.md                 ← 코스 전체 명세
    ├── env-vars-manifest.md           ← 전체 환경 변수 매니페스트
    ├── instructor-setup-guide.md      ← 강사/자기학습자 환경 설정 가이드
    ├── references/                    ← 참고 자료 (BigQuery, 비용 관리 등)
    └── research/                      ← 하니스 엔지니어링 연구 노트
```

각 모듈 디렉터리(`module-0/` ~ `module-4/`)는 독립적인 프로젝트 루트입니다:
- `pyproject.toml` — 모듈별 Python 의존성
- `dbt_project.yml` — dbt 프로젝트 설정
- `.claude/settings.json` — Claude Code 에이전트 설정
- `.github/workflows/` — GitHub Actions 워크플로 (참고용 템플릿)
- `CLAUDE.md` — 모듈별 에이전트 지침 (이전 모듈 지침 누적 포함)
- `.env.example` — 필수 환경변수 목록

---

## 참고 자료

- [코스 개요 및 강사 가이드](initialize/README.md)
- [코스 전체 명세](initialize/course-spec.md)
- [환경 변수 매니페스트](initialize/env-vars-manifest.md)
- [강사 설정 가이드](initialize/instructor-setup-guide.md)
- [GCP/BigQuery 환경 설정](initialize/references/gcp-bigquery-setup.md)
- [BigQuery 비용 관리 가이드](initialize/references/cost-management-guide.md)

---

## 라이선스

이 코스의 교육 자료는 학습 목적으로 제공됩니다.
