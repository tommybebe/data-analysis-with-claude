# 모듈 4: 종단간 통합 및 오류 처리

> 사전 구축된 하니스(훅·권한·슬래시 커맨드)를 GitHub Actions 7단계 파이프라인으로 통합하고, 오류 처리와 복구 전략을 실습합니다

**총 학습 시간**: 2.5~3.5시간

---

## 코스 전체 구조

이 모듈은 **하니스 엔지니어링 for 데이터 분석** 코스의 5개 모듈 중 하나입니다.

| 모듈 | 디렉터리 | 핵심 질문 |
|------|----------|-----------|
| 0 | `module-0-project-setup/` | 에이전트가 작업할 데이터 인프라를 어떻게 구축하는가? |
| 1 | `module-1-hooks/` | settings.json 훅으로 에이전트 정책을 어떻게 자동 실행하는가? |
| 2 | `module-2-slash-commands/` | 슬래시 커맨드로 에이전트 작업을 어떻게 명세하는가? |
| 3 | `module-3-orchestration/` | 권한과 워크플로로 에이전트 경계를 어떻게 설계하는가? |
| **4** | **`module-4-error-handling/`** (지금 여기) | **하니스 전체를 통합한 종단간 분석 워크플로를 어떻게 운영하는가?** |

> 각 모듈은 독립적으로 실행 가능합니다. 이전 모듈의 산출물은 **사전 구축 파일**로 이 디렉터리에 포함되어 있습니다.

---

## 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

1. GitHub Issue에 `auto-analyze` 라벨을 부착한 뒤 `gh run watch`로 실시간 모니터링하여, 이슈 라벨이 `stage:1-parse` → `stage:2-define` → … → `done` 순서로 전환되는 것을 이슈 타임라인에서 확인하고, dbt 모델 + marimo 노트북 소스를 포함한 PR이 자동 생성되는 것을 `gh pr list --label "auto-analyzed"` 출력으로 증명할 수 있다
2. 7단계 파이프라인의 각 단계 완료 증거(`<!-- stage:N-complete -->` HTML 앵커)가 이슈 코멘트에 순서대로 존재함을 확인할 수 있다
3. `GCP_SA_KEY`를 의도적으로 무효화하여 `stage:5-extract`에서 INFRA 오류를 발생시키고, Secret 복구 → `stage:error` 라벨 제거 → `stage:5-extract` 재부착으로 파이프라인이 해당 단계부터 재개되는 것을 검증할 수 있다
4. `evidence/query_cost_log.json`의 각 단계별 `estimated_bytes`를 합산하여 7단계 파이프라인 1회 실행의 총 BigQuery 비용을 달러로 환산하고, 비용 정책 준수 여부를 서면으로 설명할 수 있다

---

## 핵심 개념

### 종단간(End-to-End) 에이전트 기반 데이터 분석 워크플로

> **종단간 워크플로 (end-to-end workflow)**: 사람이 분석 요청(이슈)을 생성하고 결과(PR + 리포트)를 받는 것 사이의 모든 단계가, 하니스(훅·설정·권한·슬래시 커맨드) 위에서 에이전트에 의해 자동으로 수행되는 파이프라인

이 모듈에서는 사전 구축된 하니스의 **모든 구성 요소가 함께 동작하는 종단간 파이프라인**을 설계합니다:

| 사전 구축 요소 | 포함 파일 | 파이프라인에서의 역할 |
|---------------|----------|---------------------|
| 데이터 인프라 | `dbt_project.yml`, `models/`, `scripts/` | 에이전트가 사용하는 데이터/도구 인프라 |
| 훅 (자동 정책) | `.claude/hooks/bq-cost-guard.sh` 등 | 각 파이프라인 단계에서 자동 정책 실행 |
| 슬래시 커맨드 | `.claude/commands/analyze.md` 등 | 에이전트가 작업 명세를 일관되게 따르는 기반 |
| 권한 정책 | `.claude/settings.json` (`permissions`) | 에이전트가 파이프라인 내에서 적절한 권한으로만 작동 |
| **이 모듈에서 작성** | **`.github/workflows/` + `.claude/prompts/`** | **위 모든 구성 요소를 자동으로 연결하고 실행** |

### 7단계 워크플로 — 이슈에서 PR까지

| 단계 | 라벨 | 에이전트 작업 | 생성 산출물 |
|------|------|--------------|------------|
| 진입 | `auto-analyze` | 워크플로 시작 (수동 부착) | — |
| 1 | `stage:1-parse` | 이슈 본문 파싱, 구조화된 요청 객체 생성 | 파싱 결과 코멘트 |
| 2 | `stage:2-define` | 비즈니스 질문 → 분석 질문 변환 | 문제 정의서 |
| 3 | `stage:3-deliverables` | 필요 데이터/차트/테이블 목록 정의 | 산출물 체크리스트 |
| 4 | `stage:4-spec` | dbt 쿼리 계획, marimo 구조 설계 | 분석 스펙 문서 |
| 5 | `stage:5-extract` | dbt 실행, BigQuery 쿼리, 데이터 추출 | dbt 결과, 데이터 파일 |
| 6 | `stage:6-analyze` | marimo 노트북 작성, 분석·시각화 수행 | marimo `.py` 소스 |
| 7 | `stage:7-report` | HTML/PDF 내보내기, PR 자동 생성 | PR + 리포트 아티팩트 |
| 완료 | `done` | 이슈 자동 닫기 | — |

### 라벨 연쇄 전환(Label Chaining) 메커니즘

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

### 오류 처리 전략

자동화 파이프라인에서 오류는 불가피합니다. 4가지 카테고리로 분류하고, 각 카테고리별로 자동 재시도 또는 사람 개입이 필요한지 판단합니다:

| 카테고리 | 코드 | 예시 | 자동 재시도 |
|----------|------|------|-------------|
| 인프라 오류 | `INFRA` | BigQuery 인증 실패, GitHub API rate limit | ✅ (최대 3회) |
| 데이터 오류 | `DATA` | 테이블 미존재, dbt 테스트 실패 | ❌ (데이터 확인 필요) |
| 에이전트 오류 | `AGENT` | 잘못된 SQL 생성, marimo 실행 오류 | ✅ (최대 2회, 프롬프트 보강 후) |
| 워크플로 오류 | `WORKFLOW` | 라벨 전환 실패, permissions 누락 | ❌ (워크플로 수정 필요) |

> **복구 원칙**: `stage:error` 라벨을 제거하고 실패한 단계의 라벨을 재부착하면, 파이프라인이 해당 단계부터 재개됩니다. 이전 단계를 다시 실행하지 않으므로, 이미 완료된 단계의 산출물이 이슈 코멘트에 남아 있어야 합니다.

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
- `.claude/settings.json` — 훅 등록 + 권한 설정 (`permissions.allow` ≥3개, `permissions.deny` ≥3개)
- `.claude/hooks/bq-cost-guard.sh` — BigQuery 비용 가드 훅
- `.claude/hooks/dbt-auto-test.sh` — dbt 자동 컴파일 훅
- `.claude/hooks/stop-summary.sh` — 세션 종료 요약 훅

**슬래시 커맨드 계층** (사전 구축):
- `.claude/commands/analyze.md` — 분석 워크플로 커맨드
- `.claude/commands/check-cost.md` — 비용 추정 커맨드
- `.claude/commands/validate-models.md` — 모델 검증 커맨드
- `.claude/commands/generate-report.md` — 보고서 생성 커맨드

**이 모듈에서 제공하는 파일**:
- `pyproject.toml` — Python 의존성 명세
- `CLAUDE.md` — 에이전트 지시 파일
- `.env.example` — 환경 변수 템플릿
- `.gitignore` — Git 무시 규칙
- `.claude/commands/validate.md` — `/validate` 검증 커맨드

### 학습자가 직접 생성하는 파일

- `.github/workflows/auto-analyze.yml` — GitHub Actions 7단계 오케스트레이션 워크플로
- `.claude/prompts/stage-1-parse.md` ~ `stage-7-report.md` — 에이전트 단계별 프롬프트 7개
- `evidence/query_cost_log.json` — BigQuery 비용 로그
- `evidence/module-4-retrospective.md` — 파이프라인 회고 문서

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

### 활동 1: 하니스 구성 요소 통합 검증 (15~20분)

> 이 활동의 목적: 전체 파이프라인을 실행하기 전에, 사전 구축된 하니스 구성 요소가 모두 올바르게 설정되어 있는지 검증합니다.

```bash
# 사전 구축 하니스 통합 점검
echo "=== 하니스 구성 요소 통합 점검 ==="

# 훅 스크립트 존재 확인
echo "[훅] 훅 스크립트..."
ls -la .claude/hooks/bq-cost-guard.sh 2>/dev/null && echo "✅ bq-cost-guard.sh 존재" || echo "❌ bq-cost-guard.sh 없음"

# settings.json 존재 및 훅 등록 확인
echo "[설정] settings.json 훅 설정..."
python3 -c "import json; d=json.load(open('.claude/settings.json')); print('✅ hooks 존재' if 'hooks' in d else '❌ hooks 없음')"

# 슬래시 커맨드 파일 존재 확인
echo "[커맨드] 슬래시 커맨드..."
ls .claude/commands/*.md 2>/dev/null && echo "✅ 커맨드 파일 존재" || echo "❌ .claude/commands/*.md 없음"

# 권한 정책 적용 확인
echo "[권한] 권한 정책..."
python3 -c "
import json
d = json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
allow_count = len(p.get('allow', []))
deny_count = len(p.get('deny', []))
print(f'✅ allow {allow_count}개, deny {deny_count}개' if allow_count >= 3 and deny_count >= 3 else f'❌ allow {allow_count}개, deny {deny_count}개 (각 3개 이상 필요)')
"

# GitHub Secrets 확인
echo "[인프라] GitHub Secrets..."
gh secret list | grep -cE "GCP_SA_KEY|GCP_PROJECT_ID|CLAUDE_TOKEN" | xargs echo "✅ Secrets 등록 수:"
```

### 활동 2: GitHub Actions 7단계 오케스트레이션 워크플로 YAML 작성 (30~40분)

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

### 활동 3: 에이전트 단계별 프롬프트 파일 7개 설계 (25~30분)

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

### 활동 4: 전체 파이프라인 종단간 실행 (20~25분)

> 💰 **BigQuery 비용 추정**: 합성 데이터 기준 7단계 파이프라인 1회 실행 비용은 약 $0.01~$0.05입니다.

```bash
# 1. 분석 요청 이슈 생성
gh issue create \
  --title "[분석] FitTrack 2026년 1분기 DAU/MAU 트렌드 분석" \
  --body "## 분석 요청

**기간**: 2026-01-01 ~ 2026-03-31
**지표**: DAU, MAU, DAU/MAU 비율
**세분화**: 플랫폼별 (iOS, Android)
**목적**: 1분기 사용자 활동 트렌드 파악 및 리텐션 분석"

# 2. 이슈 번호 확인
ISSUE_NUMBER=$(gh issue list --limit 1 --json number -q '.[0].number')
echo "이슈 번호: #$ISSUE_NUMBER"

# 3. auto-analyze 라벨 부착 — 파이프라인 시작
gh issue edit $ISSUE_NUMBER --add-label "auto-analyze"

# 4. 워크플로 실행 실시간 모니터링
gh run watch

# 5. 이슈 라벨 전환 이력 확인
gh issue view $ISSUE_NUMBER --json labels,timelineItems
```

**관찰 초점**: 라벨이 `auto-analyze` → `stage:1-parse` → ... → `done` 순서로 정확히 전환되는가? 사전 구축된 `bq-cost-guard.sh` 훅이 단계 5 실행 시 자동으로 작동하는가?

### 활동 5: 의도적 오류 발생 및 복구 실습 (15~20분)

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

> **관찰 포인트**: 오류 코멘트에 `<!-- error-category: INFRA -->` 앵커가 포함되는지 확인합니다. 복구 후 파이프라인이 stage:5부터 재개되어 이전 단계를 반복하지 않는지 확인합니다.

### 활동 6: 파이프라인 비용 측정, 하니스 효과 회고 및 문서화 (20~25분)

```bash
# BigQuery 비용 측정
python3 -c "
import json

# evidence/query_cost_log.json에서 단계별 비용 집계
with open('evidence/query_cost_log.json') as f:
    log = json.load(f)

total_bytes = sum(entry.get('estimated_bytes', 0) for entry in log)
total_cost_usd = total_bytes / (1024**4) * 5  # on-demand: \$5/TB

print(f'총 스캔 데이터: {total_bytes / (1024**3):.2f} GB')
print(f'총 비용 (on-demand): \${total_cost_usd:.4f}')
print(f'비용 정책 (1GB 제한): {\"✅ 준수\" if total_bytes < 1024**3 else \"❌ 초과\"}')
"
```

회고 결과를 `evidence/module-4-retrospective.md`에 작성합니다:

```markdown
## 파이프라인 실행 회고 — 영역 A: 하니스 통합 효과

1. 사전 구축된 하니스 구성 요소(훅, 권한, 슬래시 커맨드) 중
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

---

## 기대 산출물

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | GitHub Actions 워크플로 YAML | `.github/workflows/auto-analyze.yml` — 7단계 라벨 분기 + 오류 처리 포함 | 하니스 설정 |
| 2 | 워크플로 라벨 11개 | GitHub 레포 라벨 — `auto-analyze`, `stage:1-parse` ~ `stage:7-report`, `done`, `stage:error`, `needs-retry` | 하니스 설정 |
| 3 | 에이전트 단계별 프롬프트 7개 | `.claude/prompts/stage-1-parse.md` ~ `stage-7-report.md` | 하니스 설정 |
| 4 | BigQuery 비용 로그 | `evidence/query_cost_log.json` | 완료 증거 |
| 5 | 파이프라인 회고 문서 | `evidence/module-4-retrospective.md` — 영역 A, B, C 작성 | 학습 기록 |

---

## 자기 점검 체크리스트

> **사용 방법**: 각 항목을 **합격(PASS) / 불합격(FAIL)** 이분법으로 평가합니다.
> 7개 항목 **모두 합격(✅)** 이어야 코스를 완료한 것으로 인정됩니다.

**[점검 1/7] 워크플로 YAML 문법 검증**

- [ ] `.github/workflows/auto-analyze.yml` 파일이 존재하며 YAML 문법 오류가 없는가?
  - **검증 명령**: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-analyze.yml'))"`
  - **✅ 합격 기준**: YAML 문법 오류 없음, `on.issues.types: [labeled]` 트리거 존재, `permissions: issues: write` 존재
  - **❌ 불합격 시 조치**: YAML 들여쓰기 오류 확인 (탭 대신 스페이스)

**[점검 2/7] 워크플로 7단계 라벨 분기 확인**

- [ ] YAML에 `stage:1-parse`부터 `stage:7-report`까지 7개 라벨 분기가 모두 존재하는가?
  - **✅ 합격 기준**: 7개 단계 라벨 모두 YAML에 참조됨
  - **❌ 불합격 시 조치**: 누락된 단계 라벨의 분기 조건 추가

**[점검 3/7] 오류 처리 로직 확인**

- [ ] YAML에 `stage:error` 라벨 처리 및 `error-category` 앵커 작성 로직이 존재하는가?
  - **✅ 합격 기준**: `stage:error` 및 `error-category` 키워드 존재
  - **❌ 불합격 시 조치**: 오류 처리 분기 추가

**[점검 4/7] 프롬프트 파일 7개 존재 확인**

- [ ] `.claude/prompts/` 디렉터리에 `stage-1-parse.md`부터 `stage-7-report.md`까지 7개 파일이 존재하는가?
  - **✅ 합격 기준**: 7개 파일 모두 존재
  - **❌ 불합격 시 조치**: 활동 3의 Claude Code 프롬프트 실행

**[점검 5/7] 프롬프트 파일 내용 검증 (stage-5 샘플)**

- [ ] `stage-5-extract.md`에 비용 제한, dbt, BigQuery 관련 내용이 포함되어 있는가?
  - **✅ 합격 기준**: 1GB 비용 제한, dbt 참조, BigQuery 참조 모두 포함
  - **❌ 불합격 시 조치**: 제약 조건 섹션 보강

**[점검 6/7] 사전 구축 하니스 통합 점검**

- [ ] 훅 3개 + 권한 정책 + 슬래시 커맨드 4개 + dbt 모델이 모두 존재하는가?
  - **✅ 합격 기준**: 4개 항목 모두 통과
  - **❌ 불합격 시 조치**: 사전 구축 파일 목록 확인 후 누락 파일 복구

**[점검 7/7] 회고 문서 존재 확인**

- [ ] `evidence/module-4-retrospective.md`가 존재하며 하니스/파이프라인/비용 내용이 포함되어 있는가?
  - **✅ 합격 기준**: 파일 존재, 관련 키워드 2개 이상 포함
  - **❌ 불합격 시 조치**: 활동 6의 회고 템플릿 참고하여 작성

> **코스 완료 조건**: 위 7개 항목 **전부 ✅ 합격** 시 코스를 완료한 것으로 인정됩니다.
> 검증 명령: `/validate` 슬래시 커맨드 실행
