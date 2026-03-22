# 모듈 3: 오케스트레이션 — GitHub Actions로 자동 분석 파이프라인 구축

> **학습 시간**: 2~3시간
> **난이도**: 중급
> **핵심 질문**: "이슈 하나로 전체 분석이 자동 실행되려면 무엇이 어떻게 연결되어야 하는가?"

---

## 학습 목표

이 모듈을 완료하면 다음을 할 수 있습니다:

- GitHub Actions와 Claude Agent SDK를 사용하여 이슈 기반 자동 분석 워크플로를 처음부터 작성할 수 있다
- 7단계 자동 분석 워크플로(문제 정의 → 산출물 명세 → 스펙 작성 → 데이터 추출 → 분석 수행 → 리포트 생성 → PR 생성)를 **라벨 연쇄 전환(label chaining)** 방식으로 구현할 수 있다
- 라벨 트리거 방식으로 워크플로 실행을 제어하고, 기본 오류 복구 전략을 설계할 수 있다

---

## 사전 조건

### 파일 준비 상태

모듈 2를 완료한 상태로, 다음 파일이 레포에 존재해야 합니다:

```
✅ AGENTS.md                                        — 에이전트 컨텍스트 (모듈 1 산출물)
✅ models/staging/sources.yml                       — 데이터 계약 포함
✅ models/marts/fct_daily_active_users.sql          — DAU 마트 모델
✅ models/marts/fct_monthly_active_users.sql        — MAU 마트 모델
✅ .github/ISSUE_TEMPLATE/analysis-request.yml     — 이슈 템플릿 (모듈 1 산출물)
✅ .claude/commands/analyze.md                      — 분석 스킬 (모듈 2 산출물)
✅ .claude/settings.json                            — 훅 설정 (모듈 2 산출물)
✅ GitHub Secrets                                   — GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_TOKEN 등록
```

`.github/workflows/auto-analyze.yml`은 **아직 없는 상태**입니다 — 이것이 모듈 3의 핵심 산출물입니다.

### 빠른 사전 확인

```bash
# 1. 필수 파일 존재 확인
for f in AGENTS.md \
          models/marts/fct_daily_active_users.sql \
          models/marts/fct_monthly_active_users.sql \
          .github/ISSUE_TEMPLATE/analysis-request.yml \
          .claude/commands/analyze.md \
          .claude/settings.json; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ $f — 없음"
done

# 2. GitHub Secrets 등록 여부 확인 (이름만, 값은 표시 안 됨)
gh secret list | grep -E "GCP_SA_KEY|GCP_PROJECT_ID|CLAUDE_TOKEN"

# 3. 아직 없어야 하는 파일 확인
[ ! -f ".github/workflows/auto-analyze.yml" ] && \
  echo "✅ auto-analyze.yml 없음 — 정상" || \
  echo "⚠️  auto-analyze.yml 이미 존재 — 이 모듈의 산출물이 미리 생성된 상태"
```

---

## 핵심 개념

이 섹션은 관찰-수정-창작 실습에 앞서 반드시 이해해야 하는 배경 지식입니다. 처음 읽을 때 100% 이해되지 않아도 괜찮습니다 — 실습 중에 다시 돌아오면서 의미가 구체화됩니다.

### 오케스트레이션 (Orchestration)이란?

**오케스트레이션(orchestration)**은 이슈 트래커의 상태를 기반으로 에이전트 작업을 **자동으로 시작, 진행, 완료**하는 제어 루프입니다. 음악의 오케스트라에서 지휘자가 여러 악기의 연주 순서와 타이밍을 조율하듯, 여기서는 하니스(harness)가 에이전트들의 실행 순서와 조건을 제어합니다.

모듈 1(스캐폴딩)과 모듈 2(스킬/훅)가 에이전트의 "환경"과 "능력"을 정의했다면, 오케스트레이션은 이 모든 것을 **연결하여 자동으로 실행**하는 계층입니다:

```
이슈 생성 + auto-analyze 라벨 부착
  → stage:1-problem 라벨 자동 부착 → GitHub Actions 트리거
    → Claude Code로 에이전트 실행 (문제 정의)
      → 단계 완료 → stage:1-problem 제거 + stage:2-deliverables 부착
        → GitHub Actions 다시 트리거 (산출물 명세)
          → ... → stage:7-pr → done
```

### 라벨 연쇄 전환 방식 (Label Chaining)

이 코스에서는 GitHub Issue의 라벨 전환으로 7단계 워크플로를 오케스트레이션합니다. 각 단계가 완료되면 **현재 라벨을 제거하고 다음 단계 라벨을 부착**하여 `labeled` 이벤트가 연쇄 트리거됩니다.

이 방식의 장점:

- **가시성(visibility)**: 이슈의 라벨만 보면 현재 어느 단계인지 즉시 파악 가능
- **추적성(traceability)**: 라벨 이력으로 전체 실행 흐름을 재구성할 수 있음
- **복구 가능성(recoverability)**: 특정 단계 실패 시 해당 단계 라벨만 다시 부착하여 재실행
- **사람 개입 없음**: 전 과정이 라벨 이벤트로 자동 진행

### 7단계 자동 워크플로 전체 지도

| 단계 | 라벨 | 실행 주체 | 산출물 |
|------|------|-----------|--------|
| 진입 | `auto-analyze` | Actions 스크립트 | 시작 코멘트 → `stage:1-problem` 부착 |
| 1 | `stage:1-problem` | Claude Code 에이전트 | `problem_statement.md` |
| 2 | `stage:2-deliverables` | Claude Code 에이전트 | 산출물 체크리스트 (Markdown + JSON) |
| 3 | `stage:3-spec` | Claude Code 에이전트 | 분석 스펙 문서 |
| 4 | `stage:4-extract` | Claude Code 에이전트 | dbt 실행 결과, 적재 데이터 확인 |
| 5 | `stage:5-analyze` | Claude Code 에이전트 | marimo 노트북 (.py) |
| 6 | `stage:6-report` | Actions 스크립트 | HTML 리포트 + 아티팩트 |
| 7 | `stage:7-pr` | Actions 스크립트 | Pull Request |
| 완료 | `done` | — | 이슈 자동 닫기 |

### Claude Agent SDK의 비대화형 실행

Claude Agent SDK는 GitHub Actions 러너에서 Claude Code를 **비대화형(non-interactive) 모드**로 실행합니다. `-p` 플래그로 프롬프트를 전달하면, 에이전트는 작업을 수행하고 exit code를 반환한 뒤 종료합니다.

```bash
# 비대화형 실행 — CI/CD 환경에서의 에이전트 호출 기본 형태
claude -p "이슈 #${ISSUE_NUMBER}의 문제를 정의하고 problem_statement.md를 생성하세요."

# 최대 턴 수 제한 (비용 및 시간 제어)
claude -p "..." --max-turns 15

# 파일에서 프롬프트 읽기 (긴 지시사항일 때 권장)
claude -p "$(cat .claude/prompts/stage-1-problem.md)"
```

> **하니스 vs 파이프라인 산출물 구분**: `auto-analyze.yml` YAML 파일, `settings.json` 훅, 라벨 설정 스크립트는 모두 **하니스 설정 파일**입니다. 반면 `problem_statement.md`, marimo 노트북, HTML 리포트는 **파이프라인 산출물** — 즉 하니스가 실행되어 생성된 결과물입니다. 이 모듈에서 작성하는 것은 하니스 설정입니다.

---

## 1단계: 관찰

> **이 단계의 목표**: 완성된 `auto-analyze.yml` 워크플로를 읽고 각 구성요소가 무엇을 하는지 설명할 수 있게 된다.

아직 자신의 워크플로를 작성하기 전에, **완성된 예시**를 먼저 꼼꼼히 읽습니다. 이 단계에서는 아무것도 수정하지 않습니다. 오직 이해만 합니다.

### 관찰 자료 1: 최소 동작 워크플로 (진입 + 1단계)

아래는 두 개의 잡(job)만 포함한 축약 버전입니다. 실제 7단계 워크플로를 이해하기 위한 발판입니다.

```yaml
# .github/workflows/auto-analyze.yml (관찰용 최소 예시)
# 이 파일은 학습을 위한 것입니다 — 아직 레포에 없는 상태입니다
name: Auto Analyze  # 워크플로 표시 이름

# 트리거 정의: 이슈에 라벨이 붙을 때만 실행
on:
  issues:
    types: [labeled]

jobs:

  # 잡 1: 'auto-analyze' 라벨이 붙으면 첫 단계로 전환
  start-pipeline:
    if: github.event.label.name == 'auto-analyze'  # 라벨 필터링
    runs-on: ubuntu-latest
    permissions:
      issues: write  # 라벨 조작 및 코멘트 게시 권한
    steps:
      - name: 파이프라인 시작 알림
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 이슈에 시작 코멘트를 게시하여 사용자에게 알림
          gh issue comment ${{ github.event.issue.number }} \
            --body "🤖 자동 분석 파이프라인을 시작합니다. 현재 단계: 문제 정의"

          # 진입 라벨 제거 후 1단계 라벨 부착 — 이것이 다음 잡을 트리거함
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "auto-analyze" \
            --add-label "stage:1-problem"

  # 잡 2: 'stage:1-problem' 라벨이 붙으면 에이전트로 문제 정의
  stage-1-problem:
    if: github.event.label.name == 'stage:1-problem'
    runs-on: ubuntu-latest
    permissions:
      contents: write  # 파일 커밋 권한
      issues: write    # 라벨 조작 및 코멘트 권한
    steps:
      - name: 레포 체크아웃
        uses: actions/checkout@v4

      - name: Claude Agent SDK 설치
        run: pip install claude-agent-sdk  # SDK 설치

      - name: Claude 인증 설정
        run: |
          # setup-token: 러너의 ~/.config/claude/에 인증 정보 기록
          # CLAUDE_TOKEN은 로컬에서 'claude login'으로 생성 후 Secret에 등록
          claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 문제 정의
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_BODY: ${{ github.event.issue.body }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 에이전트에게 이슈 본문을 바탕으로 problem_statement.md를 작성하게 함
          # --max-turns: 무한 루프 방지, 비용 상한선 역할
          claude -p "
          이슈 #${ISSUE_NUMBER}의 내용을 분석하여 problem_statement.md를 작성하세요.
          이슈 내용: ${ISSUE_BODY}
          AGENTS.md의 지시를 따르세요.
          " --max-turns 10

      - name: 산출물 커밋
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/problem_statement.md
          # 커밋이 없으면 (파일 변경 없음) 조용히 성공
          git diff --staged --quiet || \
            git commit -m "feat: 문제 정의 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 다음 단계로 라벨 전환
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 현재 라벨 제거 + 다음 단계 라벨 부착 → 연쇄 트리거
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:1-problem" \
            --add-label "stage:2-deliverables"
```

### 관찰 질문 (답하지 않아도 됨, 스스로 생각하기)

위 YAML을 읽으면서 다음을 생각해보세요:

1. `if: github.event.label.name == 'auto-analyze'` 조건이 없다면 어떤 일이 생길까?
2. `start-pipeline` 잡이 완료되면 왜 자동으로 `stage-1-problem` 잡이 실행될까?
3. `--max-turns 10`을 제거하면 어떤 위험이 생길까?
4. 단계 3(`stage:3-spec`)에서 에이전트가 실패하면 라벨이 어떤 상태로 남을까?

### 관찰 자료 2: 실패 처리 패턴 — 오류 스텝

다음은 에이전트 실행 단계에 오류 처리를 추가한 패턴입니다:

```yaml
      - name: 에이전트 실행 — 산출물 명세
        id: run-agent  # 이 스텝의 결과를 나중에 참조하기 위해 id 부여
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 에이전트 실행 — 실패 시 exit code 1 반환
          claude -p "이슈 #${ISSUE_NUMBER}의 산출물 목록을 JSON으로 작성하세요." \
            --max-turns 15
        continue-on-error: true  # 실패해도 다음 스텝 실행 (오류 처리를 위해)

      - name: 오류 처리 — 에이전트 실패 시 라벨 전환
        # 이전 스텝이 실패한 경우에만 실행
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 실패 라벨 부착으로 사람에게 알림
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:2-deliverables" \
            --add-label "stage:error"
          # 이슈에 실패 코멘트 게시
          gh issue comment ${{ github.event.issue.number }} \
            --body "❌ 2단계(산출물 명세)에서 에이전트가 실패했습니다. \
                   수동 확인 후 라벨을 다시 부착하여 재시도하세요."
          exit 1  # 잡 전체를 실패로 표시
```

### 관찰 자료 3: `.claude/settings.json` — 하니스 훅 설정

CI/CD에서 에이전트가 실행될 때 사용하는 `settings.json`도 확인합니다. 이것은 **하니스 설정 파일**의 핵심입니다:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__bash__run_command",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre_bq_cost_check.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post_verify_evidence.sh"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "mcp__bash__run_command(bq *)",
      "mcp__bash__run_command(dbt *)",
      "mcp__bash__run_command(git add *)",
      "mcp__bash__run_command(git commit *)",
      "mcp__bash__run_command(git push *)"
    ]
  }
}
```

> **하니스 설정 읽기 체크**: `PreToolUse` 훅은 `bq` 명령 실행 *전에* `pre_bq_cost_check.sh`를 실행합니다. `Stop` 훅은 에이전트가 종료할 때 `post_verify_evidence.sh`를 실행합니다. 이 두 훅의 역할 차이를 설명할 수 있다면 관찰 단계가 완료된 것입니다.

### 1단계 자기 점검

- [ ] `on: issues: types: [labeled]` 트리거가 어떤 상황에서 워크플로를 시작하는지 설명할 수 있다
- [ ] `if: github.event.label.name == 'stage:1-problem'` 조건이 없으면 무슨 일이 생기는지 설명할 수 있다
- [ ] `continue-on-error: true`와 `steps.<id>.outcome == 'failure'` 패턴의 역할을 설명할 수 있다
- [ ] `settings.json`의 훅 설정이 YAML 워크플로와 어떻게 분리된 역할을 하는지 설명할 수 있다

---

## 2단계: 수정

> **이 단계의 목표**: 불완전하거나 잘못된 워크플로를 주어진 명세에 맞게 수정하고, 그 이유를 설명할 수 있게 된다.

이 단계에서는 **의도적으로 문제가 있거나 미완성인 코드**를 받아 수정합니다. 수정 전에 먼저 무엇이 잘못되었는지 진단하고, 수정 후에는 왜 그렇게 수정했는지 주석으로 설명합니다.

### 수정 실습 A: 라벨 전환 누락 버그

아래 `stage-3-spec` 잡에는 중요한 버그가 있습니다. 찾아서 수정하세요.

**버그가 있는 코드:**

```yaml
  stage-3-spec:
    if: github.event.label.name == 'stage:3-spec'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}
      - name: 에이전트 실행 — 분석 스펙
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          claude -p "이슈 #${ISSUE_NUMBER}에 대한 분석 스펙 문서를 작성하세요." \
            --max-turns 12
      - name: 커밋
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/
          git diff --staged --quiet || \
            git commit -m "feat: 분석 스펙 — 이슈 #${{ github.event.issue.number }}"
          git push
      # ❌ 여기에 무언가 빠져 있습니다
```

**수정 후 코드 (정답 예시):**

```yaml
  stage-3-spec:
    if: github.event.label.name == 'stage:3-spec'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}
      - name: 에이전트 실행 — 분석 스펙
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          claude -p "이슈 #${ISSUE_NUMBER}에 대한 분석 스펙 문서를 작성하세요." \
            --max-turns 12
        continue-on-error: true  # 수정: 실패 시 오류 처리 스텝을 위해 필요

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:3-spec" \
            --add-label "stage:error"
          exit 1

      - name: 커밋
        if: steps.run-agent.outcome == 'success'  # 수정: 성공 시에만 커밋
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/
          git diff --staged --quiet || \
            git commit -m "feat: 분석 스펙 — 이슈 #${{ github.event.issue.number }}"
          git push

      # ✅ 수정: 라벨 전환 스텝 추가 — 이것이 없으면 워크플로가 여기서 멈춤
      - name: 다음 단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:3-spec" \
            --add-label "stage:4-extract"
```

> **수정 포인트 해설**: 원본 코드는 라벨 전환 스텝이 전혀 없었습니다. 에이전트가 성공해도 워크플로가 4단계로 진행되지 않고, 이슈에 `stage:3-spec` 라벨이 영원히 남습니다. 또한 `continue-on-error`가 없어서 에이전트 실패 시 오류 처리 경로를 탈 수 없었습니다.

### 수정 실습 B: 권한(permissions) 누락

다음 잡은 실행하면 `Resource not accessible by integration` 오류가 발생합니다. 이유를 찾고 수정하세요.

**버그가 있는 코드:**

```yaml
  stage-5-analyze:
    if: github.event.label.name == 'stage:5-analyze'
    runs-on: ubuntu-latest
    # ❌ permissions 블록이 없음
    env:
      GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4

      - name: GCP 인증 설정
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 분석 수행
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          claude -p "이슈 #${ISSUE_NUMBER}의 분석 스펙을 실행하여 marimo 노트북을 생성하세요." \
            --max-turns 20

      - name: 다음 단계로 라벨 전환
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:5-analyze" \
            --add-label "stage:6-report"
```

**수정 후 코드:**

```yaml
  stage-5-analyze:
    if: github.event.label.name == 'stage:5-analyze'
    runs-on: ubuntu-latest
    # ✅ 수정: permissions 블록 추가
    # contents: write — 분석 결과 파일 커밋
    # issues: write  — 라벨 조작 및 코멘트 게시
    permissions:
      contents: write
      issues: write
    env:
      GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4

      - name: GCP 인증 설정
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 분석 수행
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          claude -p "이슈 #${ISSUE_NUMBER}의 분석 스펙을 실행하여 marimo 노트북을 생성하세요." \
            --max-turns 20
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:5-analyze" \
            --add-label "stage:error"
          exit 1

      - name: 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add notebooks/ evidence/
          git diff --staged --quiet || \
            git commit -m "feat: 분석 수행 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 다음 단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:5-analyze" \
            --add-label "stage:6-report"
```

### 수정 실습 C: `settings.json` 권한 설정 확장

현재 `settings.json`에는 `bq query` 명령만 허용되어 있어 에이전트가 `dbt run`을 실행할 수 없습니다. `dbt run`, `dbt test`, `git add`, `git commit`, `git push`도 허용하도록 수정하세요.

**현재 설정:**

```json
{
  "permissions": {
    "allow": [
      "mcp__bash__run_command(bq query *)"
    ]
  }
}
```

**수정 후 설정:**

```json
{
  "permissions": {
    "allow": [
      "mcp__bash__run_command(bq query *)",
      "mcp__bash__run_command(bq --dry_run *)",
      "mcp__bash__run_command(dbt run *)",
      "mcp__bash__run_command(dbt test *)",
      "mcp__bash__run_command(dbt compile *)",
      "mcp__bash__run_command(git add evidence/*)",
      "mcp__bash__run_command(git add notebooks/*)",
      "mcp__bash__run_command(git commit -m *)",
      "mcp__bash__run_command(git push)"
    ],
    "deny": [
      "mcp__bash__run_command(rm -rf *)",
      "mcp__bash__run_command(git push --force *)"
    ]
  }
}
```

> **수정 포인트 해설**: `allow` 목록은 최소 권한 원칙(principle of least privilege)에 따라 에이전트가 필요한 명령만 허용합니다. `deny` 목록은 명시적으로 위험한 명령을 차단합니다. `git push --force`와 `rm -rf`는 허용해서는 안 됩니다.

### 2단계 자기 점검

- [ ] 라벨 전환 스텝이 빠진 잡이 어떤 증상을 보이는지 설명할 수 있다
- [ ] `permissions` 블록이 없는 잡에서 어떤 오류가 발생하는지 설명할 수 있다
- [ ] `continue-on-error: true`가 없을 때 오류 처리 흐름이 어떻게 달라지는지 설명할 수 있다
- [ ] `settings.json`의 `allow`와 `deny` 패턴의 차이와 우선순위를 설명할 수 있다

---

## 3단계: 창작

> **이 단계의 목표**: 7단계 전체 워크플로를 처음부터 설계하고 작성하여 실제로 이슈 하나를 자동으로 처리할 수 있게 한다.

관찰과 수정으로 쌓인 이해를 바탕으로, 이제 **완전한 `auto-analyze.yml`**을 직접 작성합니다. 이 파일이 모듈 3의 최종 산출물입니다.

### 창작 실습: 완전한 7단계 워크플로 작성

아래의 뼈대(skeleton)를 완성하세요. `# TODO:` 주석이 있는 모든 부분을 채워야 합니다.

**1. 라벨 설정 스크립트 먼저 작성**

워크플로를 만들기 전에, 필요한 GitHub 라벨을 레포에 생성하는 스크립트를 작성합니다:

```bash
#!/bin/bash
# scripts/setup-labels.sh
# 목적: 7단계 자동 분석 파이프라인에 필요한 GitHub 라벨 생성
# 실행: bash scripts/setup-labels.sh
# 비용: 없음 (GitHub API 호출만 사용)

set -e  # 명령 실패 시 즉시 종료

# GitHub CLI 인증 확인
if ! gh auth status &>/dev/null; then
  echo "❌ GitHub CLI 인증 필요: gh auth login 실행 후 재시도"
  exit 1
fi

echo "🏷️  라벨 생성 시작..."

# 진입/완료 라벨
gh label create "auto-analyze"   --color "0075ca" --description "분석 파이프라인 진입 트리거" --force
gh label create "done"           --color "0e8a16" --description "파이프라인 완료"             --force

# 7단계 실행 라벨
gh label create "stage:1-problem"      --color "e4e669" --description "1단계: 문제 정의"     --force
gh label create "stage:2-deliverables" --color "e4e669" --description "2단계: 산출물 명세"   --force
gh label create "stage:3-spec"         --color "e4e669" --description "3단계: 분석 스펙"     --force
gh label create "stage:4-extract"      --color "fbca04" --description "4단계: 데이터 추출"   --force
gh label create "stage:5-analyze"      --color "fbca04" --description "5단계: 분석 수행"     --force
gh label create "stage:6-report"       --color "0075ca" --description "6단계: 리포트 생성"   --force
gh label create "stage:7-pr"           --color "0075ca" --description "7단계: PR 생성"       --force

# 오류/재시도 라벨
gh label create "stage:error"    --color "d93f0b" --description "파이프라인 오류 — 수동 확인 필요" --force
gh label create "needs-retry"    --color "d93f0b" --description "재시도 요청"                      --force

echo "✅ 라벨 생성 완료"
```

**2. 완전한 워크플로 파일 작성**

```yaml
# .github/workflows/auto-analyze.yml
# 목적: GitHub 이슈 기반 7단계 자동 분석 파이프라인
# 트리거: 이슈에 특정 라벨이 부착될 때
# 비용 고려: 각 에이전트 잡은 --max-turns으로 BigQuery 쿼리 횟수를 간접 제한

name: Auto Analyze Pipeline

on:
  issues:
    types: [labeled]

# 동일 이슈에 대한 중복 실행 방지
# concurrency 그룹: 이슈 번호 기준으로 그룹화
concurrency:
  group: analyze-issue-${{ github.event.issue.number }}
  cancel-in-progress: false  # 진행 중인 잡은 취소하지 않음 (데이터 손상 방지)

jobs:

  # ──────────────────────────────────────────────
  # 진입: auto-analyze 라벨 → 1단계 시작
  # ──────────────────────────────────────────────
  start-pipeline:
    if: github.event.label.name == 'auto-analyze'
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: 파이프라인 시작 코멘트 게시
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 이슈 작성자에게 파이프라인 시작을 알리는 코멘트 게시
          gh issue comment ${{ github.event.issue.number }} \
            --body "## 🤖 자동 분석 파이프라인 시작

          **이슈 #${{ github.event.issue.number }}** 에 대한 자동 분석을 시작합니다.

          진행 단계:
          1. 🔍 문제 정의
          2. 📋 산출물 명세
          3. 📐 분석 스펙 작성
          4. 🗄️  데이터 추출
          5. 📊 분석 수행
          6. 📄 리포트 생성
          7. 🔀 PR 생성

          각 단계가 완료되면 이슈 라벨이 업데이트됩니다."

      - name: 1단계 라벨로 전환
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 진입 라벨 제거 → 1단계 라벨 부착 → 연쇄 트리거 시작
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "auto-analyze" \
            --add-label "stage:1-problem"

  # ──────────────────────────────────────────────
  # 1단계: 문제 정의
  # 산출물: evidence/problem_statement.md
  # 예상 에이전트 비용: 쿼리 없음, 토큰 약 2,000개 소비
  # ──────────────────────────────────────────────
  stage-1-problem:
    if: github.event.label.name == 'stage:1-problem'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: Claude Agent SDK 설치
        run: pip install claude-agent-sdk

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 문제 정의
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
          ISSUE_BODY: ${{ github.event.issue.body }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 에이전트에게 이슈 정보를 전달하여 problem_statement.md 생성
          # 이 단계는 BigQuery 쿼리를 실행하지 않으므로 비용 없음
          claude -p "
          이슈 제목: ${ISSUE_TITLE}
          이슈 번호: #${ISSUE_NUMBER}
          이슈 내용:
          ${ISSUE_BODY}

          위 정보를 바탕으로 evidence/problem_statement.md를 작성하세요.
          AGENTS.md의 문제 정의 템플릿을 따르세요.
          " --max-turns 8
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:1-problem" \
            --add-label "stage:error"
          gh issue comment ${{ github.event.issue.number }} \
            --body "❌ **1단계(문제 정의) 실패**. Actions 로그를 확인한 후, \`stage:1-problem\` 라벨을 다시 부착하여 재시도하세요."
          exit 1

      - name: 산출물 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/
          git diff --staged --quiet || \
            git commit -m "feat(analysis): 1단계 문제 정의 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 2단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:1-problem" \
            --add-label "stage:2-deliverables"

  # ──────────────────────────────────────────────
  # 2단계: 산출물 명세
  # 산출물: evidence/deliverables.md, evidence/deliverables.json
  # 예상 에이전트 비용: 쿼리 없음, 토큰 약 1,500개 소비
  # ──────────────────────────────────────────────
  stage-2-deliverables:
    if: github.event.label.name == 'stage:2-deliverables'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: Claude Agent SDK 설치
        run: pip install claude-agent-sdk
      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 산출물 명세
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # problem_statement.md를 읽어 구체적인 산출물 목록 생성
          # deliverables.json은 다음 단계들이 참조하는 기계 판독 가능한 명세
          claude -p "
          evidence/problem_statement.md를 읽고, 이 분석의 산출물을 명세하세요.
          evidence/deliverables.md (사람이 읽는 형식)과
          evidence/deliverables.json (기계 판독 형식)을 생성하세요.
          이슈 번호: #${ISSUE_NUMBER}
          " --max-turns 10
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:2-deliverables" \
            --add-label "stage:error"
          exit 1

      - name: 산출물 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/
          git diff --staged --quiet || \
            git commit -m "feat(analysis): 2단계 산출물 명세 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 3단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:2-deliverables" \
            --add-label "stage:3-spec"

  # ──────────────────────────────────────────────
  # 3단계: 분석 스펙 작성
  # 산출물: evidence/analysis_spec.md
  # 예상 에이전트 비용: BQ dry_run 1~2회 (~$0.00), 토큰 약 3,000개 소비
  # ──────────────────────────────────────────────
  stage-3-spec:
    if: github.event.label.name == 'stage:3-spec'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    env:
      GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4

      - name: GCP 인증 설정
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Python 및 도구 설치
        run: |
          pip install claude-agent-sdk dbt-bigquery

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 분석 스펙 작성
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 스펙 작성 단계에서 에이전트는 BQ dry_run으로 비용을 추정하고
          # models/ 디렉토리를 탐색하여 어떤 dbt 모델을 사용할지 계획함
          claude -p "
          evidence/deliverables.json과 models/ 디렉토리를 분석하여
          evidence/analysis_spec.md를 작성하세요.
          - 사용할 dbt 모델 목록
          - BQ 쿼리 예상 비용 (dry_run 실행 후 기록)
          - marimo 노트북 구조 개요
          이슈 번호: #${ISSUE_NUMBER}
          " --max-turns 15
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:3-spec" \
            --add-label "stage:error"
          exit 1

      - name: 산출물 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/
          git diff --staged --quiet || \
            git commit -m "feat(analysis): 3단계 분석 스펙 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 4단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:3-spec" \
            --add-label "stage:4-extract"

  # ──────────────────────────────────────────────
  # 4단계: 데이터 추출
  # 산출물: 업데이트된 dbt 모델, evidence/extraction_summary.md
  # 예상 BQ 비용: dbt 모델 실행 ~5 GB 처리 → ~$0.031 (파티션 필터 적용 시)
  # ──────────────────────────────────────────────
  stage-4-extract:
    if: github.event.label.name == 'stage:4-extract'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    env:
      GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4

      - name: GCP 인증 설정
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: 도구 설치
        run: pip install claude-agent-sdk dbt-bigquery

      - name: dbt 의존성 설치
        run: uv run dbt deps --project-dir . --profiles-dir .

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 데이터 추출
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 이 단계에서 실제 BigQuery 비용이 발생함
          # settings.json의 PreToolUse 훅이 각 BQ 쿼리 전 비용 체크를 수행
          claude -p "
          evidence/analysis_spec.md에 명시된 dbt 모델을 실행하고
          데이터 추출을 수행하세요.
          - dbt run --select <필요한 모델>
          - 결과를 evidence/extraction_summary.md에 기록
          - 처리된 바이트와 예상 비용을 반드시 기록
          이슈 번호: #${ISSUE_NUMBER}
          " --max-turns 20
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:4-extract" \
            --add-label "stage:error"
          exit 1

      - name: 산출물 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add evidence/ models/
          git diff --staged --quiet || \
            git commit -m "feat(analysis): 4단계 데이터 추출 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 5단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:4-extract" \
            --add-label "stage:5-analyze"

  # ──────────────────────────────────────────────
  # 5단계: 분석 수행
  # 산출물: notebooks/analysis_<issue_number>.py (marimo 노트북)
  # 예상 BQ 비용: 분석 쿼리 ~10 GB → ~$0.063
  # ──────────────────────────────────────────────
  stage-5-analyze:
    if: github.event.label.name == 'stage:5-analyze'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
    env:
      GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4

      - name: GCP 인증 설정
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: 도구 설치
        run: pip install claude-agent-sdk marimo

      - name: Claude 인증
        run: claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      - name: 에이전트 실행 — 분석 수행
        id: run-agent
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # marimo 노트북을 .py 파일로 생성
          # marimo run 명령으로 노트북을 실행하여 결과 HTML 생성
          claude -p "
          evidence/analysis_spec.md와 evidence/extraction_summary.md를 읽고
          notebooks/analysis_${{ github.event.issue.number }}.py marimo 노트북을 작성하세요.
          노트북에는 다음을 포함하세요:
          - BigQuery에서 데이터 읽기
          - 주요 메트릭 계산 및 시각화
          - 핵심 인사이트 요약
          작성 후 marimo export html notebooks/analysis_${{ github.event.issue.number }}.py \
            -o evidence/report_${{ github.event.issue.number }}.html 을 실행하세요.
          이슈 번호: #${ISSUE_NUMBER}
          " --max-turns 25
        continue-on-error: true

      - name: 오류 처리
        if: steps.run-agent.outcome == 'failure'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:5-analyze" \
            --add-label "stage:error"
          exit 1

      - name: 산출물 커밋
        if: steps.run-agent.outcome == 'success'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add notebooks/ evidence/
          git diff --staged --quiet || \
            git commit -m "feat(analysis): 5단계 분석 수행 — 이슈 #${{ github.event.issue.number }}"
          git push

      - name: 6단계로 라벨 전환
        if: steps.run-agent.outcome == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:5-analyze" \
            --add-label "stage:6-report"

  # ──────────────────────────────────────────────
  # 6단계: 리포트 생성 및 Actions 아티팩트 업로드
  # 산출물: HTML 리포트 (Actions 아티팩트로 업로드)
  # 비용: GitHub Actions 스토리지 (~500 KB HTML 기준 무시 가능)
  # ──────────────────────────────────────────────
  stage-6-report:
    if: github.event.label.name == 'stage:6-report'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: 리포트 파일 확인
        id: check-report
        run: |
          # 에이전트가 생성한 HTML 리포트 파일 존재 확인
          REPORT="evidence/report_${{ github.event.issue.number }}.html"
          if [ -f "$REPORT" ]; then
            echo "report_exists=true" >> $GITHUB_OUTPUT
            echo "report_path=$REPORT" >> $GITHUB_OUTPUT
            echo "✅ 리포트 파일 확인: $REPORT"
          else
            echo "report_exists=false" >> $GITHUB_OUTPUT
            echo "⚠️  리포트 파일 없음 — 이전 단계를 확인하세요"
          fi

      - name: Actions 아티팩트 업로드
        if: steps.check-report.outputs.report_exists == 'true'
        uses: actions/upload-artifact@v4
        with:
          name: analysis-report-issue-${{ github.event.issue.number }}
          path: ${{ steps.check-report.outputs.report_path }}
          retention-days: 30  # 30일 보관

      - name: 이슈에 리포트 링크 코멘트
        if: steps.check-report.outputs.report_exists == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 리포트 다운로드 링크를 이슈 코멘트로 게시
          gh issue comment ${{ github.event.issue.number }} \
            --body "📊 **분석 리포트 생성 완료**

          리포트는 [Actions 아티팩트](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})에서 다운로드할 수 있습니다.
          (보관 기간: 30일)"

      - name: 7단계로 라벨 전환
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:6-report" \
            --add-label "stage:7-pr"

  # ──────────────────────────────────────────────
  # 7단계: PR 생성
  # 산출물: Pull Request (노트북 + 증거 파일 포함)
  # 비용: 없음
  # ──────────────────────────────────────────────
  stage-7-pr:
    if: github.event.label.name == 'stage:7-pr'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write  # PR 생성 권한
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 전체 이력 가져오기 (브랜치 생성을 위해)

      - name: PR 브랜치 생성
        id: create-branch
        run: |
          # 이슈 번호 기반 브랜치명 생성
          BRANCH="analysis/issue-${{ github.event.issue.number }}"
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          # 브랜치가 이미 존재하면 재사용, 없으면 생성
          git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
          echo "branch=$BRANCH" >> $GITHUB_OUTPUT

      - name: PR 생성
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRANCH="${{ steps.create-branch.outputs.branch }}"

          # 이미 PR이 존재하면 건너뜀
          EXISTING_PR=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo "")

          if [ -z "$EXISTING_PR" ]; then
            gh pr create \
              --title "분석 결과: 이슈 #${{ github.event.issue.number }}" \
              --body "## 자동 분석 결과

          이슈 #${{ github.event.issue.number }} 에 대한 자동 분석 결과입니다.

          ### 포함 파일
          - \`evidence/problem_statement.md\` — 문제 정의
          - \`evidence/deliverables.md\` — 산출물 목록
          - \`evidence/analysis_spec.md\` — 분석 스펙
          - \`notebooks/analysis_${{ github.event.issue.number }}.py\` — marimo 노트북
          - \`evidence/report_${{ github.event.issue.number }}.html\` — HTML 리포트

          Closes #${{ github.event.issue.number }}" \
              --head "$BRANCH" \
              --base main
          else
            echo "PR already exists: #$EXISTING_PR"
          fi

      - name: 완료 라벨 부착 및 이슈 닫기
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # 마지막 단계 라벨 제거 + 완료 표시
          gh issue edit ${{ github.event.issue.number }} \
            --remove-label "stage:7-pr" \
            --add-label "done"

          # 이슈 자동 닫기 (PR이 병합되면 자동으로 닫히지만 명시적으로 닫음)
          gh issue close ${{ github.event.issue.number }} \
            --comment "✅ **자동 분석 파이프라인 완료.** PR이 생성되었습니다."
```

### 창작 완료 검증

워크플로 파일 작성 후 다음을 확인합니다:

```bash
# 1. YAML 문법 검증 (Python yaml 모듈 사용)
python3 -c "
import yaml, sys
with open('.github/workflows/auto-analyze.yml') as f:
    yaml.safe_load(f)
print('✅ YAML 문법 유효')
"

# 2. 7단계 잡이 모두 있는지 확인
for stage in "start-pipeline" "stage-1-problem" "stage-2-deliverables" \
             "stage-3-spec" "stage-4-extract" "stage-5-analyze" \
             "stage-6-report" "stage-7-pr"; do
  grep -q "$stage:" .github/workflows/auto-analyze.yml && \
    echo "✅ $stage" || echo "❌ $stage 없음"
done

# 3. 라벨 설정 스크립트 실행 (실제 레포에 라벨 생성)
bash scripts/setup-labels.sh

# 4. 테스트 이슈 생성으로 파이프라인 트리거
gh issue create \
  --title "[테스트] 지난 7일 DAU 추이 분석" \
  --body "## 분석 요청

**분석 목적**: DAU 주간 추이 확인
**분석 기간**: 최근 7일
**기대 산출물**: 일별 DAU 추이 차트, 최고/최저 DAU 날짜 식별

## 배경
최근 마케팅 캠페인 이후 사용자 활동 변화를 확인하고자 합니다."

# 이슈 번호 확인 후 auto-analyze 라벨 부착
ISSUE_NUMBER=$(gh issue list --limit 1 --json number --jq '.[0].number')
gh issue edit $ISSUE_NUMBER --add-label "auto-analyze"
echo "🚀 파이프라인 트리거 완료 — 이슈 #$ISSUE_NUMBER"
```

---

## 모듈 자기 점검 체크리스트

아래 항목을 직접 검증하세요. **모든 항목이 ✅일 때만 모듈 3을 완료한 것으로 간주합니다.**

### 하니스 설정 파일 검증

- [ ] **PASS**: `.github/workflows/auto-analyze.yml` 파일이 존재한다
  - **FAIL 기준**: 파일이 없거나 YAML 파싱 오류가 있다
  - **FAIL 시 조치**: 창작 실습의 YAML을 그대로 복사하여 저장 후 Python으로 검증

- [ ] **PASS**: 워크플로에 7개의 잡(start-pipeline, stage-1 ~ stage-7)이 모두 있다
  - **FAIL 기준**: `grep "stage-[0-9]-" .github/workflows/auto-analyze.yml | wc -l` 결과가 7 미만
  - **FAIL 시 조치**: 누락된 잡 섹션을 창작 실습 예시에서 복사하여 추가

- [ ] **PASS**: 각 잡에 `permissions` 블록이 있고 `issues: write`가 포함되어 있다
  - **FAIL 기준**: `grep -c "issues: write" .github/workflows/auto-analyze.yml` 결과가 7 미만
  - **FAIL 시 조치**: 수정 실습 B의 설명에 따라 permissions 블록 추가

- [ ] **PASS**: 각 에이전트 실행 스텝에 `--max-turns` 옵션이 있다
  - **FAIL 기준**: `grep "claude -p" .github/workflows/auto-analyze.yml | grep -v "max-turns"` 결과 존재
  - **FAIL 시 조치**: 모든 `claude -p` 명령에 `--max-turns N` 추가

- [ ] **PASS**: `scripts/setup-labels.sh`가 실행 가능하고 9개의 라벨을 생성한다
  - **FAIL 기준**: 스크립트 실행 오류 또는 `gh label list | grep "stage:" | wc -l` 결과가 7 미만
  - **FAIL 시 조치**: 창작 실습의 setup-labels.sh 내용을 사용

### 오케스트레이션 동작 검증

- [ ] **PASS**: 테스트 이슈에 `auto-analyze` 라벨 부착 시 Actions 워크플로가 자동 트리거된다
  - **FAIL 기준**: `gh run list --limit 3`에서 새 실행이 나타나지 않음
  - **FAIL 시 조치**: 워크플로 파일이 `main` 브랜치에 커밋되었는지, `on: issues: types: [labeled]` 트리거가 있는지 확인

- [ ] **PASS**: `start-pipeline` 잡 완료 후 이슈에 `stage:1-problem` 라벨이 부착된다
  - **FAIL 기준**: 잡 성공 후에도 이슈 라벨이 `auto-analyze`로 남아 있음
  - **FAIL 시 조치**: `start-pipeline` 잡의 라벨 전환 스텝 실행 로그 확인

- [ ] **PASS**: 에이전트 실행 실패 시 `stage:error` 라벨이 부착된다
  - **검증 방법**: `CLAUDE_TOKEN` Secret을 일시적으로 잘못된 값으로 변경하여 인증 실패 유도
  - **FAIL 기준**: 실패 시 이슈 라벨 상태 변화가 없음
  - **FAIL 시 조치**: `continue-on-error: true`와 오류 처리 스텝이 올바르게 설정되었는지 확인

### 개념 이해 검증

- [ ] **PASS**: "라벨 연쇄 전환 방식이 상태 머신을 구현하는 방식"을 동료에게 2분 안에 설명할 수 있다
  - **FAIL 기준**: GitHub Issues 상태, `labeled` 이벤트 트리거, 잡 필터링 중 하나라도 설명 못함
  - **FAIL 시 조치**: 핵심 개념 섹션의 "오케스트레이션이란?" 다시 읽기

- [ ] **PASS**: `auto-analyze.yml` (하니스 설정)과 `evidence/` 폴더 파일 (파이프라인 산출물)의 차이를 설명할 수 있다
  - **FAIL 기준**: 두 가지를 구분하지 못하거나 혼용함
  - **FAIL 시 조치**: 핵심 개념 섹션의 "하니스 vs 파이프라인 산출물" 박스 다시 읽기

---

## 다음 모듈

모듈 4에서는 이 워크플로가 실패하거나 예상보다 많은 비용을 사용할 때 어떻게 감지하고 대응하는지를 다룹니다. 모듈 3에서 만든 `auto-analyze.yml`에 오류 처리와 비용 모니터링 훅을 추가합니다.
