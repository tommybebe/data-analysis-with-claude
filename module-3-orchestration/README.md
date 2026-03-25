# 모듈 3: 권한 오케스트레이션

> Claude Code 권한 정책으로 에이전트 경계를 설계하는 방법을 배웁니다

**총 학습 시간**: 1.5~2시간

---

## 코스 전체 구조

이 모듈은 **하니스 엔지니어링 for 데이터 분석** 코스의 5개 모듈 중 하나입니다.

| 모듈 | 디렉터리 | 핵심 질문 |
|------|----------|-----------|
| 0 | `module-0-project-setup/` | 에이전트가 작업할 데이터 인프라를 어떻게 구축하는가? |
| 1 | `module-1-hooks/` | settings.json 훅으로 에이전트 정책을 어떻게 자동 실행하는가? |
| 2 | `module-2-slash-commands/` | 슬래시 커맨드로 에이전트 작업을 어떻게 명세하는가? |
| **3** | **`module-3-orchestration/`** (지금 여기) | **권한과 워크플로로 에이전트 경계를 어떻게 설계하는가?** |
| 4 | `module-4-error-handling/` | 하니스 전체를 통합한 종단간 분석 워크플로를 어떻게 운영하는가? |

> 각 모듈은 독립적으로 실행 가능합니다. 이전 모듈의 산출물은 **사전 구축 파일**로 이 디렉터리에 포함되어 있습니다.

---

## 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

1. `.claude/settings.json`의 `permissions.allow`와 `permissions.deny` 섹션이 각각 3개 이상의 규칙을 포함하도록 작성하고, JSON 문법 오류 없이 출력되는 것을 확인할 수 있다
2. `claude "git push --force origin main을 실행해줘"` 실행 시 에이전트가 거부 메시지를 출력하며 실행을 거부하는 것을 확인할 수 있다
3. GitHub Actions 워크플로 YAML(`.github/workflows/auto-analyze.yml`)에서 `permissions:` 키를 작성하고, 각 권한이 필요한 이유를 설명할 수 있다
4. 로컬 개발 환경과 CI 환경의 권한 설계가 의도적으로 다르게 설계된 이유를 문서로 작성할 수 있다

---

## 핵심 개념

### 권한 오케스트레이션 (Permissions Orchestration)

> **권한 오케스트레이션**: 에이전트가 작업 맥락(로컬 개발 / CI 파이프라인)에 따라 서로 다른 권한 경계를 갖도록 정책을 설계하고 조정하는 행위

이 디렉터리의 `.claude/settings.json`에는 기본적인 `permissions.allow`와 `permissions.deny`가 이미 설정되어 있습니다. 이 모듈에서는 **권한이 전체 하니스 오케스트레이션과 어떻게 상호작용하는가**를 배웁니다:

- 로컬에서 대화형으로 사용할 때와 GitHub Actions에서 자동 실행될 때 동일한 권한을 줘도 되는가?
- 단계별 파이프라인에서 각 에이전트 단계에 필요한 권한은 어떻게 최소화하는가?
- GitHub Actions의 `permissions:` 키와 Claude Code의 `permissions.allow/deny`는 어떻게 연관되는가?

### Claude Code 권한 계층 구조

Claude Code 권한은 세 가지 범위(scope)에서 적용됩니다:

```
글로벌 설정 (~/.claude/settings.json)
  └─ 모든 Claude Code 세션에 적용되는 기본 권한

프로젝트 설정 (.claude/settings.json)  ← 이 코스에서 주로 작성
  └─ 해당 레포지토리에서 Claude Code 실행 시 적용
  └─ 글로벌 설정보다 구체적이므로 우선 적용

로컬 설정 (.claude/settings.local.json)
  └─ 개별 개발자의 로컬 환경에만 적용 (gitignore 권장)
```

### `permissions.allow`와 `permissions.deny`의 역할 분담

| 구분 | 역할 | 설계 원칙 |
|------|------|-----------|
| `allow` (허용 목록) | 에이전트가 실행 가능한 명령의 **화이트리스트** | 데이터 분석 작업에 필요한 최소 권한만 포함 |
| `deny` (거부 목록) | 에이전트가 절대 실행할 수 없는 명령의 **블랙리스트** | 되돌리기 어려운(irreversible) 작업을 명시적으로 차단 |
| 우선순위 | `deny` > `allow` | deny 목록에 있으면 allow에 있어도 차단 |

### GitHub Actions `permissions:` 키 — CI 환경 권한 분리

Claude Code의 `permissions.allow/deny`가 **에이전트 도구 사용 권한**을 제어한다면, GitHub Actions의 `permissions:` 키는 **워크플로가 GitHub API에 접근할 수 있는 권한**을 제어합니다:

| GitHub Actions `permissions:` 키 | 필요한 이유 |
|----------------------------------|------------|
| `issues: write` | 각 단계 완료 후 이슈 코멘트 작성, 라벨 전환 |
| `contents: write` | 분석 결과 파일 커밋, 브랜치 푸시 |
| `pull-requests: write` | 자동 PR 생성 및 설명 작성 |

### 로컬 vs CI 환경 권한 비교

| 항목 | 로컬 개발 (`.claude/settings.json`) | CI 환경 (GitHub Actions) |
|------|-------------------------------------|--------------------------|
| 사용 맥락 | 개발자가 대화형으로 사용 | 자동화 파이프라인에서 비대화형 실행 |
| 권한 주체 | 개별 개발자 Claude Code 세션 | GitHub Actions Runner + Claude Agent SDK |
| 위험 수준 | 개발자가 즉시 오류 확인 가능 | 오류 시 자동 확산 위험, 더 엄격한 제한 필요 |
| `git push` | `git push origin HEAD:*` 허용 | `contents: write`로 워크플로가 제어 |
| 비용 제한 | `BQ_COST_LIMIT_BYTES` 환경변수 | 동일한 훅 스크립트가 CI에서도 실행됨 |

> **핵심 설계 판단**: CI 환경에서는 사람이 실시간으로 감독하지 않으므로, 로컬보다 **더 엄격한** 권한 경계가 필요합니다.

---

## 사전 구축 파일 vs 학습자 생성 파일

### 사전 구축 파일 (이 디렉터리에 포함)

**데이터 인프라** (사전 구축):
- `dbt_project.yml`, `packages.yml` — dbt 프로젝트 설정
- `models/staging/*` — 스테이징 모델 및 소스 선언
- `models/marts/*` — 마트 모델 (DAU, MAU, 리텐션)
- `scripts/*` — 합성 데이터 생성 및 BigQuery 적재
- `AGENTS.md` — 에이전트 규칙

**훅 기반 정책 계층** (사전 구축):
- `.claude/settings.json` — 훅 등록 + 기초 권한 설정 (이 모듈에서 권한 섹션을 강화)
- `.claude/hooks/bq-cost-guard.sh` — BigQuery 비용 가드 훅
- `.claude/hooks/dbt-auto-test.sh` — dbt 자동 컴파일 훅
- `.claude/hooks/stop-summary.sh` — 세션 종료 요약 훅

**슬래시 커맨드 계층** (사전 구축):
- `.claude/commands/analyze.md` — 분석 워크플로 커맨드
- `.claude/commands/check-cost.md` — 비용 추정 커맨드
- `.claude/commands/validate-models.md` — 모델 검증 커맨드
- `.claude/commands/generate-report.md` — 보고서 생성 커맨드

**이 모듈 제공 파일**:
- `pyproject.toml` — Python 의존성 명세
- `CLAUDE.md` — 에이전트 지시 파일
- `.env.example` — 환경 변수 템플릿
- `.gitignore` — Git 무시 규칙
- `.claude/commands/validate.md` — `/validate` 검증 커맨드

### 학습자가 직접 생성/수정하는 파일

- `.claude/settings.json` — `permissions.allow` (≥3개) 및 `permissions.deny` (≥3개) 규칙 강화
- `.github/workflows/auto-analyze.yml` — GitHub Actions 워크플로 (초안 또는 완성본)
- `evidence/module-3-permissions-rationale.md` — 권한 설계 근거 문서
- `evidence/module-3-permissions-retrospective.md` — 모듈 회고 기록

---

## 환경 설정

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집기로 열고 실제 값 입력
```

**필수 변수:**
- `GCP_PROJECT_ID` — Google Cloud 프로젝트 ID
- `GOOGLE_APPLICATION_CREDENTIALS` — GCP 서비스 계정 키 파일 절대 경로
- `GITHUB_REPOSITORY` — GitHub 리포지토리 경로 (owner/repo 형식)

### 2. Python 의존성 설치

```bash
uv sync
```

### 3. dbt 프로필 설정

```bash
cp profiles.yml.example profiles.yml
# profiles.yml에 실제 GCP 프로젝트 정보 입력
```

### 4. dbt 의존성 설치 및 환경 검증

```bash
uv run dbt deps
uv run dbt debug
```

---

## 활동

### 활동 1: Claude Code 권한 모델 구조 탐색 및 설정 파일 계층 이해 (15~20분)

현재 레포의 Claude Code 설정 파일 현황을 파악합니다:

```bash
# 전역 설정 파일 확인 (모든 세션에 적용)
cat ~/.claude/settings.json 2>/dev/null || echo "전역 설정 없음"

# 프로젝트 설정 파일 확인 (이 레포에만 적용)
cat .claude/settings.json 2>/dev/null || echo "프로젝트 설정 없음"

# 현재 settings.json의 permissions 섹션 확인
python3 -m json.tool .claude/settings.json | grep -A 20 '"permissions"'
```

사전 구축된 권한 현황을 점검하고, 이 모듈에서 추가로 설계할 부분을 파악합니다.

### 활동 2: 데이터 분석 에이전트를 위한 허용 규칙(allow) 설계 및 구현 (20~25분)

FitTrack 데이터 분석 에이전트에게 필요한 최소 권한을 설계합니다:

```bash
claude "현재 .claude/settings.json을 분석하고, FitTrack 데이터 분석 에이전트가
필요한 최소 권한을 permissions.allow 섹션에 추가해줘.

필요한 작업 유형:
1. BigQuery 쿼리 실행 (bq query)
2. dbt 모델 실행/테스트/컴파일 (dbt run, dbt test, dbt compile)
3. marimo 노트북 실행 및 HTML/PDF 내보내기
4. Git 작업 (add, commit, push)
5. GitHub CLI로 이슈 코멘트, 라벨 관리, PR 생성

각 규칙에 왜 이 권한이 필요한지 설명하고,
최소 권한 원칙(principle of least privilege)을 적용해줘.

수정 후 python -m json.tool .claude/settings.json으로 문법 검증해줘."
```

### 활동 3: 위험 작업 차단을 위한 거부 규칙(deny) 구현 및 동작 검증 (20~25분)

되돌리기 어려운(irreversible) 작업을 차단하는 거부 규칙을 구현합니다:

```bash
# deny 설정 후 검증 — git push --force 차단 확인
claude "git push --force origin main 명령을 실행해줘"
# 기대 출력: Permission denied 또는 거부 메시지

# bq rm 차단 확인
claude "bq rm fittrack_raw.raw_events 테이블을 삭제해줘"
# 기대 출력: 거부 메시지
```

> **관찰 포인트**: 에이전트가 거부 메시지를 받았을 때 어떻게 반응하는지 관찰하세요. 좋은 에이전트는 대안을 제시하고, 나쁜 에이전트는 우회를 시도합니다.

### 활동 4: GitHub Actions `permissions:` 키 설계 (15~20분)

GitHub Actions 워크플로 YAML에서 CI 환경의 권한을 설계합니다. `.github/workflows/auto-analyze.yml` 파일을 생성하고 `permissions:` 섹션을 작성합니다.

권한 설계 문서를 `evidence/module-3-permissions-rationale.md`에 작성합니다:

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

### 활동 5: 로컬 vs CI 다중 환경 권한 정책 설계 (15~20분)

동일한 에이전트 코드가 두 가지 맥락에서 실행될 때의 권한 차이를 설계합니다:

| 실행 맥락 | 설명 | 권한 설계 방향 |
|-----------|------|---------------|
| **개발자 로컬** | 분석가가 탐색적 분석 시 Claude Code 대화형 사용 | 더 많은 도구 허용, 빠른 반복 개발 지원 |
| **CI/CD 파이프라인** | GitHub Actions에서 이슈 라벨 트리거로 자동 실행 | 최소 권한, 명시적 단계, 감사 추적 |

> **설계 원칙**: `deny` 목록은 로컬과 CI 모두에서 동일하게 유지합니다. `allow` 목록은 CI에서 더 제한적일 수 있습니다.

### 활동 6: 권한 경계 종합 테스트 및 회고 (10~15분)

현재까지 구현한 권한 정책 전체를 검증합니다:

```bash
echo "=== 권한 정책 검증 ==="

# 1. JSON 문법 검증
python3 -m json.tool .claude/settings.json > /dev/null && echo "✅ JSON 문법 유효" || echo "❌ JSON 문법 오류"

# 2. allow 규칙 수 확인
python3 -c "import json; d=json.load(open('.claude/settings.json')); print(f'허용 규칙 수: {len(d.get(\"permissions\",{}).get(\"allow\",[]))}개')"

# 3. deny 규칙 수 확인
python3 -c "import json; d=json.load(open('.claude/settings.json')); print(f'거부 규칙 수: {len(d.get(\"permissions\",{}).get(\"deny\",[]))}개')"
```

회고 질문을 `evidence/module-3-permissions-retrospective.md`에 기록합니다:

1. 권한 정책을 설계하는 과정에서 가장 판단하기 어려웠던 부분은 무엇인가?
2. 사전 구축 파일에 이미 기초적인 권한이 설정되어 있었는데, 이 모듈에서 추가적으로 설계한 부분은 무엇인가?
3. GitHub Actions의 `permissions:` 키와 Claude Code의 `permissions.allow/deny`가 서로 어떻게 보완적으로 작동하는지 한 문단으로 설명하라.

---

## 기대 산출물

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | 권한 정책이 포함된 settings.json | `.claude/settings.json` — allow ≥3개, deny ≥3개 | 하니스 설정 |
| 2 | 권한 설계 근거 문서 | `evidence/module-3-permissions-rationale.md` | 하니스 문서화 |
| 3 | GitHub Actions 권한 키 포함 YAML | `.github/workflows/auto-analyze.yml` | 하니스 설정 |
| 4 | 회고 문서 | `evidence/module-3-permissions-retrospective.md` | 학습 기록 |

---

## 자기 점검 체크리스트

> **사용 방법**: 각 항목을 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다.
> 5개 항목 **모두 합격(✅)** 이어야 이 모듈을 완료한 것입니다.

**[점검 1/5] 허용/거부 규칙 구현 확인**

- [ ] `.claude/settings.json`에 `permissions.allow`와 `permissions.deny`가 각각 3개 이상의 규칙을 포함하고 있는가?
  - **검증 명령**: `python3 -m json.tool .claude/settings.json | grep -c '"Bash'`
  - **✅ 합격 기준**: JSON 문법 오류 없음, allow와 deny 각각 3개 이상 규칙 존재
  - **❌ 불합격 시 조치**: 활동 2, 3의 예시를 참고하여 규칙 추가

**[점검 2/5] 거부 규칙 동작 검증**

- [ ] `claude "git push --force origin main을 실행해줘"` 실행 시 에이전트가 실행을 거부하는가?
  - **✅ 합격 기준**: 출력에 거부 표현이 포함됨 (실제 `git push --force`가 실행되지 않음)
  - **❌ 불합격 시 조치**: deny 목록에 `"Bash(git push --force:*)"` 확인 → Claude Code 재시작

**[점검 3/5] GitHub Actions 권한 키 설정**

- [ ] `.github/workflows/auto-analyze.yml`에 `permissions:` 섹션이 존재하며, `issues: write`와 `contents: write`가 포함되어 있는가?
  - **검증 명령**: `grep -A 5 'permissions:' .github/workflows/auto-analyze.yml`
  - **✅ 합격 기준**: `issues: write`와 `contents: write` 두 항목이 모두 포함됨
  - **❌ 불합격 시 조치**: 활동 4의 권한 설정 추가

**[점검 4/5] 권한 설계 근거 문서화**

- [ ] `evidence/module-3-permissions-rationale.md`가 존재하며, 로컬 vs CI 비교 내용이 포함되어 있는가?
  - **✅ 합격 기준**: 파일 존재, "로컬", "CI", "GitHub Actions" 중 2개 이상 포함
  - **❌ 불합격 시 조치**: 활동 4의 Claude Code 프롬프트 실행

**[점검 5/5] 핵심 개념 이해 확인**

- [ ] `.claude/settings.json`의 `permissions.allow/deny`와 GitHub Actions `permissions:` 키의 차이를 설명할 수 있는가?
  - **✅ 합격 기준**: "A는 에이전트 셸 명령 범위를 제어, B는 GitHub API 접근 범위를 제어"라는 내용이 답변에 포함됨
  - **❌ 불합격 시 조치**: 핵심 개념의 "Claude Code 권한 계층 구조"와 "GitHub Actions `permissions:` 키" 섹션 재학습

> **모듈 완료 조건**: 위 5개 항목 **전부 ✅ 합격** 시 이 모듈이 완료된 것입니다.
> 검증 명령: `/validate` 슬래시 커맨드 실행
