# GitHub Actions 워크플로 사양서

> 라벨 트리거 기반 7단계 자동 분석 파이프라인 — 설계 사양 및 구현 가이드

---

## 1. 워크플로 개요

### 목적

GitHub Issue에 `auto-analyze` 라벨을 부착하면, 사람의 개입 없이 이슈 파싱부터 최종 리포트 생성·PR 제출까지 **7단계를 자동으로 순차 실행**하는 GitHub Actions 워크플로입니다.

### 아키텍처

```
사용자 ──(라벨 부착)──→ GitHub Issue
                          │
                          ▼
                    GitHub Actions
                    (labeled 이벤트)
                          │
                   ┌──────┴──────┐
                   │ orchestrate │ ← 단일 Job, 라벨 조건 분기
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        auto-analyze  stage:1~7     done
        (진입 전환)   (에이전트 실행) (이슈 닫기)
              │           │
              └───────────┘
                    │
              라벨 제거 + 다음 라벨 부착
                    │
              labeled 이벤트 재발생
                    │
              GitHub Actions 연쇄 트리거
```

### 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **라벨 연쇄 전환** | 각 단계 완료 시 현재 라벨 제거 → 다음 라벨 부착 → `labeled` 이벤트 연쇄 트리거 |
| **단일 워크플로 파일** | `.github/workflows/auto-analyze.yml` 하나로 전체 7단계 제어 |
| **사람 개입 없음** | human-in-the-loop 체크포인트 없이 전 과정 자동 진행 |
| **이슈 코멘트 기반 상태 전달** | 단계 간 산출물은 구조화된 이슈 코멘트로 전달 |
| **GitHub Secret 기반 인증** | GCP 서비스 계정 + Claude 토큰은 모두 Repository Secret |

---

## 2. 트리거 조건 상세

### 이벤트 유형

```yaml
on:
  issues:
    types: [labeled]
```

| 속성 | 값 | 설명 |
|------|----|------|
| 이벤트 | `issues` | GitHub Issue 상태 변경 이벤트 |
| 액션 타입 | `labeled` | 라벨이 **부착**될 때만 트리거 (`unlabeled`, `opened` 등은 무시) |
| 대상 브랜치 | 해당 없음 | `issues` 이벤트는 브랜치와 무관 (기본 브랜치의 워크플로 파일 사용) |

### 실행 조건 (`if` 필터)

```yaml
jobs:
  orchestrate:
    if: |
      github.event.label.name == 'auto-analyze' ||
      startsWith(github.event.label.name, 'stage:')
```

**필터 동작**:

| 부착된 라벨 | `if` 평가 결과 | 동작 |
|-------------|---------------|------|
| `auto-analyze` | `true` | 워크플로 실행 (진입 전환) |
| `stage:1-parse` | `true` | 워크플로 실행 (단계 1) |
| `stage:5-extract` | `true` | 워크플로 실행 (단계 5) |
| `stage:error` | `true` | 워크플로 실행 (but 내부에 해당 `if` 없으므로 건너뜀) |
| `bug` | `false` | 워크플로 **미실행** |
| `enhancement` | `false` | 워크플로 **미실행** |
| `done` | `false` | 워크플로 **미실행** (종료 라벨은 `stage:` 접두어 없음) |
| `needs-retry` | `false` | 워크플로 **미실행** (재시도는 실패 단계 라벨 재부착으로 처리) |

> **주의**: `stage:error` 라벨도 `startsWith` 조건에 매칭되어 워크플로가 트리거됩니다. 하지만 내부 step-level `if` 조건에 `stage:error`에 해당하는 분기가 없으므로, 모든 step이 건너뛰어져 실질적으로 no-op 실행됩니다. 비용 최적화를 위해 job-level에서 추가 필터링할 수 있습니다:

```yaml
# 개선된 if 조건 (stage:error 제외)
if: |
  github.event.label.name == 'auto-analyze' ||
  (startsWith(github.event.label.name, 'stage:') &&
   github.event.label.name != 'stage:error')
```

### `labeled` 이벤트 컨텍스트 객체

워크플로 내에서 접근 가능한 이벤트 페이로드:

```yaml
# 주요 컨텍스트 변수
github.event.label.name        # 방금 부착된 라벨 이름 (예: "stage:3-deliverables")
github.event.issue.number      # 이슈 번호 (예: 42)
github.event.issue.title       # 이슈 제목
github.event.issue.body        # 이슈 본문 (Markdown)
github.event.issue.user.login  # 이슈 작성자
github.event.sender.login      # 라벨 부착자 (bot 또는 GitHub Actions일 수 있음)
```

---

## 3. 라벨 네이밍 규칙

### 네이밍 컨벤션

```
[카테고리]:[순서]-[영문동사/명사]
```

| 규칙 | 예시 | 설명 |
|------|------|------|
| 접두어 `stage:` | `stage:1-parse` | 워크플로 실행 단계를 나타냄 |
| 순서 번호 포함 | `stage:3-deliverables` | 실행 순서를 명시적으로 표현 |
| 소문자 + 하이픈 구분 | `auto-analyze` | GitHub 라벨 관례 준수 |
| 영문 단어 사용 | `parse`, `define`, `extract` | 코드/API 호환성 확보 |
| 특수 라벨에 `stage:` 미사용 | `auto-analyze`, `done` | 진입/종료 라벨은 트리거 제어용 |

### 라벨 카탈로그

#### 워크플로 제어 라벨 (11개)

| 순서 | 라벨 | 색상 코드 | 색상 의미 | 용도 |
|------|------|-----------|-----------|------|
| 0 | `auto-analyze` | `#0E8A16` | 🟢 초록 | 사용자가 수동 부착하는 워크플로 진입점 |
| 1 | `stage:1-parse` | `#1D76DB` | 🔵 파랑 | 이슈 본문 → 구조화된 JSON 파싱 |
| 2 | `stage:2-define` | `#1D76DB` | 🔵 파랑 | 비즈니스 질문 → 분석 질문 변환 |
| 3 | `stage:3-deliverables` | `#1D76DB` | 🔵 파랑 | 산출물 목록 정의 (차트, 테이블 등) |
| 4 | `stage:4-spec` | `#1D76DB` | 🔵 파랑 | dbt 쿼리 계획 + marimo 구조 설계 |
| 5 | `stage:5-extract` | `#5319E7` | 🟣 보라 | dbt 모델 실행, 데이터 추출 |
| 6 | `stage:6-analyze` | `#5319E7` | 🟣 보라 | marimo 노트북 작성, 분석/시각화 |
| 7 | `stage:7-report` | `#5319E7` | 🟣 보라 | HTML/PDF 내보내기, PR 생성 |
| — | `done` | `#0E8A16` | 🟢 초록 | 워크플로 정상 완료, 이슈 자동 닫기 |
| — | `stage:error` | `#D93F0B` | 🔴 빨강 | 에이전트 실행 오류 표시 |
| — | `needs-retry` | `#FBCA04` | 🟡 노랑 | 재시도 대기 상태 표시 |

#### 색상 체계

```
초록 (#0E8A16) ─── 워크플로 시작/끝 (auto-analyze, done)
파랑 (#1D76DB) ─── 설계 단계 (stage 1~4): 분석 계획 수립
보라 (#5319E7) ─── 실행 단계 (stage 5~7): 데이터 처리 및 산출물 생성
빨강 (#D93F0B) ─── 오류 (stage:error)
노랑 (#FBCA04) ─── 주의/대기 (needs-retry)
```

#### 라벨 일괄 등록 스크립트

```bash
#!/bin/bash
# scripts/setup-labels.sh
# 워크플로 라벨 일괄 생성 (기존 라벨 존재 시 --force로 덮어쓰기)

set -euo pipefail

LABELS=(
  "auto-analyze|0E8A16|자동 분석 워크플로 진입점"
  "stage:1-parse|1D76DB|단계 1: 이슈 파싱"
  "stage:2-define|1D76DB|단계 2: 문제 정의"
  "stage:3-deliverables|1D76DB|단계 3: 산출물 명세"
  "stage:4-spec|1D76DB|단계 4: 스펙 작성"
  "stage:5-extract|5319E7|단계 5: 데이터 추출"
  "stage:6-analyze|5319E7|단계 6: 분석 수행"
  "stage:7-report|5319E7|단계 7: 리포트 생성"
  "done|0E8A16|워크플로 완료"
  "stage:error|D93F0B|단계 실행 오류"
  "needs-retry|FBCA04|재시도 필요"
)

for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<< "$entry"
  gh label create "$name" --color "$color" --description "$desc" --force
  echo "✓ 라벨 생성: $name"
done

echo ""
echo "총 ${#LABELS[@]}개 라벨 등록 완료"
echo "확인: gh label list --search 'stage:'"
```

---

## 4. 워크플로 디스패치 설정

### 파일 경로 및 기본 설정

```yaml
# 파일: .github/workflows/auto-analyze.yml
name: Auto Analyze

on:
  issues:
    types: [labeled]
```

### Job 설정

```yaml
jobs:
  orchestrate:
    # 라벨 필터: auto-analyze 또는 stage: 접두어 (stage:error 제외)
    if: |
      github.event.label.name == 'auto-analyze' ||
      (startsWith(github.event.label.name, 'stage:') &&
       github.event.label.name != 'stage:error')
    runs-on: ubuntu-latest
    timeout-minutes: 30

    permissions:
      contents: write       # 브랜치 생성, 커밋, 푸시
      issues: write          # 라벨 변경, 코멘트 작성, 이슈 닫기
      pull-requests: write   # PR 생성

    env:
      GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
      CURRENT_LABEL: ${{ github.event.label.name }}
```

### 권한 (`permissions`) 상세

| 권한 | 값 | 사용처 |
|------|----|--------|
| `contents` | `write` | `git push`, 브랜치 생성, 파일 커밋 |
| `issues` | `write` | `addLabels`, `removeLabel`, `createComment`, `update`(닫기) |
| `pull-requests` | `write` | `gh pr create` |

> **보안 참고**: `GITHUB_TOKEN`의 기본 권한은 `read`이므로, 명시적으로 `write`를 선언해야 합니다. 최소 권한 원칙에 따라 필요 없는 권한(예: `packages`, `deployments`)은 선언하지 않습니다.

### GitHub Secrets 요구사항

| Secret 이름 | 용도 | 설정 방법 |
|-------------|------|-----------|
| `GCP_SA_KEY` | BigQuery 인증용 GCP 서비스 계정 JSON 키 | GCP 콘솔에서 키 생성 → `gh secret set GCP_SA_KEY < key.json` |
| `GCP_PROJECT_ID` | BigQuery 프로젝트 ID | `gh secret set GCP_PROJECT_ID --body "my-project-id"` |
| `CLAUDE_TOKEN` | Claude Agent SDK 인증 토큰 | `claude login` → 토큰 복사 → `gh secret set CLAUDE_TOKEN` |
| `GITHUB_PAT` | PR 생성 시 Git 작업 인증 (PAT 또는 GitHub App 토큰) | GitHub 설정에서 PAT 생성 → `gh secret set GITHUB_PAT` |

> **`GITHUB_TOKEN` vs `GITHUB_PAT`**: 기본 `GITHUB_TOKEN`으로 생성한 라벨 이벤트는 워크플로를 **재트리거하지 않습니다** (무한 루프 방지 정책). 라벨 연쇄 전환을 위해 `GITHUB_PAT` (또는 GitHub App 토큰)을 사용해야 합니다.

---

## 5. 라벨 전환 메커니즘

### 전환 흐름도

```
사용자 ──(auto-analyze 부착)──→ [워크플로 실행 #1]
                                     │
                                     ▼ (stage:1-parse 부착, PAT 사용)
                               [워크플로 실행 #2]
                                     │ (에이전트: 이슈 파싱)
                                     ▼ (stage:1-parse 제거 + stage:2-define 부착)
                               [워크플로 실행 #3]
                                     │ (에이전트: 문제 정의)
                                     ▼ (stage:2-define 제거 + stage:3-deliverables 부착)
                                    ...
                               [워크플로 실행 #8]
                                     │ (에이전트: 리포트 생성 + PR)
                                     ▼ (stage:7-report 제거 + done 부착)
                               [이슈 자동 닫기]
```

> **중요**: 각 단계마다 **독립된 워크플로 실행**이 발생합니다. 총 8회 (진입 1회 + 단계 7회) 실행됩니다.

### 전환 매핑 테이블

```javascript
// actions/github-script에서 사용하는 라벨 전환 매핑
const transitions = {
  'stage:1-parse':        'stage:2-define',
  'stage:2-define':       'stage:3-deliverables',
  'stage:3-deliverables': 'stage:4-spec',
  'stage:4-spec':         'stage:5-extract',
  'stage:5-extract':      'stage:6-analyze',
  'stage:6-analyze':      'stage:7-report',
  'stage:7-report':       'done'
};
```

### 전환 실행 코드 (actions/github-script)

```javascript
// 라벨 전환 step — 모든 단계 완료 후 공통 실행
const label = '${{ env.CURRENT_LABEL }}';
const transitions = { /* 위 매핑 */ };
const nextLabel = transitions[label];

if (!nextLabel) {
  console.log(`전환 대상 없음: ${label}`);
  return;
}

// 1. 현재 라벨 제거
try {
  await github.rest.issues.removeLabel({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: ${{ env.ISSUE_NUMBER }},
    name: label
  });
} catch (e) {
  console.log(`라벨 제거 실패 (이미 제거됨): ${label}`);
}

// 2. 다음 라벨 부착 (PAT 사용 → labeled 이벤트 발생 → 연쇄 트리거)
// 주의: GITHUB_TOKEN으로는 연쇄 트리거 불가, PAT/GitHub App 필요
const octokit = github.getOctokit('${{ secrets.GITHUB_PAT }}');
await octokit.rest.issues.addLabels({
  owner: context.repo.owner,
  repo: context.repo.repo,
  issue_number: ${{ env.ISSUE_NUMBER }},
  labels: [nextLabel]
});

// 3. done 라벨이면 이슈 자동 닫기
if (nextLabel === 'done') {
  await github.rest.issues.update({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: ${{ env.ISSUE_NUMBER }},
    state: 'closed',
    state_reason: 'completed'
  });
}
```

### `GITHUB_TOKEN` vs `GITHUB_PAT` — 연쇄 트리거 제약

GitHub는 **무한 루프 방지**를 위해 `GITHUB_TOKEN`으로 수행한 API 호출이 새로운 워크플로를 트리거하지 못하도록 제한합니다.

| 인증 방식 | 라벨 부착 시 `labeled` 이벤트 발생 | 워크플로 연쇄 트리거 |
|-----------|----------------------------------|---------------------|
| `GITHUB_TOKEN` | 예 | **아니오** (워크플로 재트리거 차단) |
| `GITHUB_PAT` (Personal Access Token) | 예 | **예** |
| GitHub App Token | 예 | **예** |

따라서 라벨 부착 API 호출에는 반드시 `GITHUB_PAT` 또는 GitHub App 토큰을 사용해야 합니다.

```yaml
# 라벨 부착 step에서 PAT 사용 예시
- name: 라벨 전환
  uses: actions/github-script@v7
  env:
    GH_PAT: ${{ secrets.GITHUB_PAT }}
  with:
    github-token: ${{ secrets.GITHUB_PAT }}  # 기본 GITHUB_TOKEN 대신 PAT 사용
    script: |
      // addLabels 호출 → labeled 이벤트 발생 → 다음 워크플로 트리거
      await github.rest.issues.addLabels({ ... });
```

---

## 6. Step-level 라벨 조건 분기

### 분기 패턴

단일 Job 내에서 `if` 조건으로 현재 라벨에 해당하는 step만 실행합니다:

```yaml
steps:
  # ── 공통 환경 설정 (모든 라벨에서 실행) ──
  - name: 레포 체크아웃
    uses: actions/checkout@v4

  - name: Python 설정
    uses: actions/setup-python@v5
    with:
      python-version: '3.12'

  - name: uv 설치 및 의존성 설치
    run: |
      curl -LsSf https://astral.sh/uv/install.sh | sh
      uv sync

  - name: GCP 인증 설정
    run: |
      echo '${{ secrets.GCP_SA_KEY }}' > /tmp/gcp-key.json
      echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json" >> $GITHUB_ENV

  - name: Claude Agent SDK 인증
    run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

  - name: 이슈 본문 및 코멘트 수집
    id: context
    uses: actions/github-script@v7
    with:
      script: |
        // 이슈 본문 + 이전 단계 코멘트 수집
        // ...

  # ── 라벨별 단계 실행 (조건 분기) ──
  - name: "진입: auto-analyze → stage:1-parse"
    if: env.CURRENT_LABEL == 'auto-analyze'
    # ...

  - name: "단계 1: 이슈 파싱"
    if: env.CURRENT_LABEL == 'stage:1-parse'
    # ...

  - name: "단계 2: 문제 정의"
    if: env.CURRENT_LABEL == 'stage:2-define'
    # ...

  # ... (단계 3~7)

  # ── 공통 후처리 (단계 완료 시 실행) ──
  - name: 이슈에 단계 완료 코멘트 기록
    if: env.CURRENT_LABEL != 'auto-analyze'
    # ...

  - name: 라벨 전환
    if: env.CURRENT_LABEL != 'auto-analyze'
    # ...

  # ── 오류 처리 ──
  - name: 오류 시 stage:error 라벨 부착
    if: failure()
    # ...

  # ── 아티팩트 (stage:7-report에서만) ──
  - name: HTML/PDF 리포트 아티팩트 업로드
    if: env.CURRENT_LABEL == 'stage:7-report'
    # ...
```

### Step 실행 매트릭스

각 워크플로 실행에서 실제로 실행되는 step:

| Step | `auto-analyze` | `stage:1` | `stage:2` | `stage:3` | `stage:4` | `stage:5` | `stage:6` | `stage:7` |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 레포 체크아웃 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Python 설정 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| uv 설치 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| GCP 인증 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Claude SDK 인증 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 이슈 컨텍스트 수집 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 진입 전환 | ✓ | — | — | — | — | — | — | — |
| 단계 N 에이전트 | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 완료 코멘트 | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 라벨 전환 | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 아티팩트 업로드 | — | — | — | — | — | — | — | ✓ |

---

## 7. 오류 처리 및 복구

### 오류 발생 시 동작

```yaml
- name: 오류 시 stage:error 라벨 부착
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      // stage:error 라벨 추가 (실패한 단계 라벨은 유지)
      await github.rest.issues.addLabels({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: ${{ env.ISSUE_NUMBER }},
        labels: ['stage:error']
      });

      // 오류 상세 코멘트 작성
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: ${{ env.ISSUE_NUMBER }},
        body: [
          '## ❌ 단계 실행 오류',
          '',
          `실패 라벨: \`${{ env.CURRENT_LABEL }}\``,
          `워크플로 실행: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
          '',
          '### 재시도 방법',
          '1. Actions 로그에서 오류 원인 확인',
          '2. `stage:error` 라벨 제거',
          `3. \`${{ env.CURRENT_LABEL }}\` 라벨을 제거 후 다시 부착하여 해당 단계부터 재실행`
        ].join('\n')
      });
```

### 복구 흐름

```
정상 흐름:  stage:3-deliverables → (성공) → stage:4-spec
오류 흐름:  stage:3-deliverables → (실패) → stage:3-deliverables + stage:error
복구 흐름:
  1. 사용자가 Actions 로그에서 오류 확인
  2. stage:error 라벨 제거 (수동)
  3. stage:3-deliverables 라벨 제거 (수동)
  4. stage:3-deliverables 라벨 재부착 (수동) → 해당 단계부터 재실행
```

### 타임아웃 설정

```yaml
jobs:
  orchestrate:
    timeout-minutes: 30  # Job 전체 타임아웃
```

| 단계 | 예상 소요 시간 | 타임아웃 위험도 |
|------|-------------|---------------|
| stage:1-parse | ~1분 | 낮음 |
| stage:2-define | ~2분 | 낮음 |
| stage:3-deliverables | ~2분 | 낮음 |
| stage:4-spec | ~3분 | 낮음 |
| stage:5-extract | ~5분 (dbt run 포함) | 중간 |
| stage:6-analyze | ~5분 (marimo 작성) | 중간 |
| stage:7-report | ~5분 (export + PR) | 중간 |

> 각 단계는 독립된 워크플로 실행이므로, 30분 타임아웃은 단일 단계에 적용됩니다. 전체 7단계 합산이 아닙니다.

---

## 8. 비용 및 실행 제어

### GitHub Actions 사용량

| 항목 | 값 | 비고 |
|------|----|------|
| 워크플로 실행 횟수 | 분석 요청 1건당 8회 | 진입 1 + 단계 7 |
| 러너 | `ubuntu-latest` | GitHub-hosted, 무료 플랜 2,000분/월 |
| 예상 소요 시간 | 총 ~25분/요청 | 환경 설정 오버헤드 포함 |

### Claude Agent SDK 비용 제어

```yaml
# 각 단계별 max-turns 제한 권장값
- name: "단계 1: 이슈 파싱"
  run: claude -p "..." --max-turns 5    # 단순 파싱, 턴 수 적게

- name: "단계 5: 데이터 추출"
  run: claude -p "..." --max-turns 15   # dbt 실행 포함, 턴 수 넉넉히

- name: "단계 6: 분석 수행"
  run: claude -p "..." --max-turns 20   # marimo 작성, 가장 복잡
```

### 동시 실행 제한 (Concurrency)

동일 이슈에 대해 여러 워크플로가 동시 실행되는 것을 방지합니다:

```yaml
concurrency:
  group: auto-analyze-${{ github.event.issue.number }}
  cancel-in-progress: false  # 진행 중인 실행을 취소하지 않음 (라벨 연쇄 보호)
```

> **`cancel-in-progress: false`가 중요한 이유**: `true`로 설정하면 이전 단계 실행이 다음 단계에 의해 취소될 수 있습니다. 라벨 전환 직후 새 워크플로가 시작되면서 이전 워크플로(라벨 전환 step 실행 중)를 취소하면, 코멘트 기록이나 정리 작업이 누락될 수 있습니다.

---

## 9. 단계 간 산출물 전달 규약

### 이슈 코멘트 형식

```markdown
## Stage N 완료: [단계 이름]

### 산출물
- [산출물 파일 경로 또는 내용 요약]

### 완료 증거
- [검증 결과 — dbt 테스트, dry-run 바이트, 파일 생성 확인 등]

### 다음 단계 입력
- [다음 단계에서 사용할 핵심 정보 요약]

<!-- stage:N-complete -->
```

### 파싱 앵커

`<!-- stage:N-complete -->` HTML 코멘트는 다음 단계 에이전트가 이전 산출물을 프로그래밍 방식으로 검색하기 위한 앵커입니다.

```javascript
// 이슈 코멘트에서 이전 단계 산출물 수집
const comments = await github.rest.issues.listComments({ ... });
const stageComments = comments.data
  .filter(c => c.body.includes('stage:') && c.body.includes('-complete'))
  .map(c => c.body)
  .join('\n---\n');
```

### 파일 시스템 산출물 경로

| 단계 | 산출물 파일 | 형식 |
|------|-----------|------|
| 1 | `.analysis/request.json` | JSON |
| 2 | `.analysis/problem_statement.md` | Markdown |
| 3 | `.analysis/deliverables.json` | JSON |
| 4 | `.analysis/spec.md` | Markdown |
| 5 | `evidence/dbt_test_results.json` | JSON |
| 6 | `analyses/analysis_*.py` | Python (marimo) |
| 7 | `reports/*.html`, `reports/*.pdf` | HTML/PDF |

> **주의**: `.analysis/` 디렉토리의 파일은 워크플로 실행 간 **공유되지 않습니다**. 각 워크플로 실행은 새로운 러너에서 시작하므로, 이전 단계의 파일 산출물은 이슈 코멘트를 통해 전달해야 합니다. 다만 Git 커밋을 통해 레포에 저장된 파일은 다음 실행의 checkout에서 접근 가능합니다.

---

## 10. 검증 체크리스트

### 워크플로 파일 검증

- [ ] `.github/workflows/auto-analyze.yml` 파일이 존재하는가?
  - 검증: `ls .github/workflows/auto-analyze.yml`
- [ ] YAML 문법 오류가 없는가?
  - 검증: `actionlint .github/workflows/auto-analyze.yml` 또는 GitHub Actions UI에서 확인
- [ ] `on.issues.types`에 `labeled`가 설정되어 있는가?
  - 검증: YAML 파일에서 `on:` 섹션 확인
- [ ] Job `if` 조건이 `auto-analyze`와 `stage:` 접두어를 모두 포함하는가?
  - 검증: `if:` 조건문에 두 패턴 존재 확인

### 라벨 등록 검증

- [ ] 11개 라벨이 모두 등록되어 있는가?
  - 검증: `gh label list | grep -c 'stage:\|auto-analyze\|done\|needs-retry'` 결과가 11인지 확인
- [ ] 각 라벨의 색상이 색상 체계에 맞는가?
  - 검증: `gh label list --json name,color` 출력 비교

### 트리거 검증

- [ ] `auto-analyze` 라벨 부착 시 워크플로가 실행되는가?
  - 검증: 테스트 이슈에 라벨 부착 → Actions 탭에서 실행 확인
- [ ] `stage:1-parse` 라벨 부착 시 연쇄 트리거가 발생하는가?
  - 검증: 이슈 Activity 로그에서 `stage:1-parse` → `stage:2-define` 전환 확인
- [ ] `bug` 등 관련 없는 라벨은 워크플로를 트리거하지 않는가?
  - 검증: 무관한 라벨 부착 후 Actions 탭에서 실행 없음 확인

### 연쇄 전환 검증

- [ ] 라벨 부착에 `GITHUB_PAT`를 사용하고 있는가?
  - 검증: 워크플로 YAML에서 라벨 전환 step의 `github-token` 설정 확인
- [ ] `done` 라벨 부착 시 이슈가 자동으로 닫히는가?
  - 검증: 워크플로 완료 후 이슈 상태 확인

### 오류 처리 검증

- [ ] `failure()` 조건에서 `stage:error` 라벨이 부착되는가?
  - 검증: 의도적으로 오류 발생시켜 라벨 확인
- [ ] 오류 코멘트에 실패 단계와 Actions 로그 링크가 포함되는가?
  - 검증: 오류 코멘트 내용 확인
