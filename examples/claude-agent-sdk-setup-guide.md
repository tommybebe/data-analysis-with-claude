# Claude Agent SDK 설정 가이드

> 이 문서는 GitHub Actions CI/CD 환경에서 Claude Agent SDK를 설정하고 운영하는 방법을 상세히 다룹니다.
> 대상: 데이터 분석 하니스 엔지니어링 과정 수강생 (모듈 0, 모듈 3에서 참조)

---

## 1. Claude Agent SDK 개요

Claude Agent SDK는 **GitHub Actions 러너에서 Claude Code를 프로그래밍 방식으로 실행**할 수 있게 해주는 도구입니다. 로컬 환경에서 대화형으로 사용하는 Claude Code와 달리, CI/CD 파이프라인에서는 비대화형(non-interactive) 모드로 실행되며, `claude setup-token` 명령으로 인증을 사전에 설정합니다.

### 주요 용도 (데이터 분석 워크플로)

| 용도 | 설명 |
|------|------|
| 이슈 파싱 | GitHub Issue 본문을 구조화된 분석 요청으로 변환 |
| dbt 모델 생성 | 분석 스펙에 따라 dbt SQL 모델 자동 작성 |
| marimo 노트북 생성 | 분석 결과를 시각화하는 marimo 노트북 자동 작성 |
| PR 생성 | 분석 산출물을 포함한 Pull Request 자동 생성 |

---

## 2. 사전 요구사항

### 2.1 Claude Code Pro/Max 구독

Claude Agent SDK를 사용하려면 **Claude Code Pro 또는 Max 구독**이 필요합니다. 구독 플랜에 따라 API 사용량 한도가 다릅니다.

```
# 구독 상태 확인 (로컬 환경)
claude --version
```

### 2.2 로컬 환경에서 Claude Code 설치

```bash
# npm으로 Claude Code 설치
npm install -g @anthropic-ai/claude-code

# 설치 확인
claude --version
```

> **참고**: GitHub Actions 러너에서는 워크플로 내에서 Claude Code를 설치합니다 (섹션 5 참조).

---

## 3. `claude setup-token` 인증 흐름

### 3.1 인증 토큰 생성

`claude setup-token`은 Claude Code가 비대화형 환경에서 인증할 수 있도록 **토큰을 사전에 설정**하는 명령입니다.

```bash
# 토큰 설정 (인증 토큰을 인자로 전달)
claude setup-token <YOUR_TOKEN>
```

### 3.2 인증 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    인증 흐름 (CI/CD 환경)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 사전 준비 (로컬, 1회)                                        │
│     ┌──────────────┐                                            │
│     │ claude login  │ → 브라우저 인증 → 토큰 획득                 │
│     └──────┬───────┘                                            │
│            │                                                    │
│            ▼                                                    │
│     ┌──────────────────────────┐                                │
│     │ GitHub Secret에 토큰 저장  │                               │
│     │ (CLAUDE_TOKEN)            │                               │
│     └──────────┬───────────────┘                                │
│                │                                                │
│  2. CI/CD 실행 시 (자동, 매 실행)                                 │
│                ▼                                                │
│     ┌──────────────────────────────────────────┐               │
│     │ claude setup-token ${{ secrets.CLAUDE_TOKEN }}│            │
│     └──────────┬───────────────────────────────┘               │
│                │                                                │
│                ▼                                                │
│     ┌──────────────────────────────┐                            │
│     │ Claude Code 비대화형 실행 가능  │                           │
│     │ (claude -p "프롬프트...")      │                           │
│     └──────────────────────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 토큰 생성 단계별 절차

#### 단계 1: 로컬에서 Claude Code 로그인

```bash
# Claude Code에 로그인 (브라우저 기반 OAuth)
claude login

# 로그인 상태 확인
claude whoami
```

로그인 후 토큰이 `~/.claude/` 디렉토리에 저장됩니다.

#### 단계 2: API 토큰 확인

Claude Code Pro/Max 구독에서 제공하는 인증 토큰을 확인합니다:

```bash
# 현재 인증 정보 확인
claude auth status
```

#### 단계 3: GitHub Secret에 토큰 등록

```bash
# GitHub CLI로 Secret 등록 (권장)
gh secret set CLAUDE_TOKEN --body "<YOUR_CLAUDE_TOKEN>"

# 또는 GitHub 웹 UI에서 등록:
# Repository → Settings → Secrets and variables → Actions → New repository secret
# Name: CLAUDE_TOKEN
# Value: <토큰 값 붙여넣기>
```

> **보안 주의**: 토큰을 코드에 직접 포함하거나, 로그에 출력하지 마세요.
> GitHub Secret은 로그에서 자동으로 마스킹(`***`)됩니다.

---

## 4. GitHub Actions에서의 토큰 관리

### 4.1 Secret 구성 전체 목록

데이터 분석 하니스 워크플로에 필요한 전체 Secret 목록:

| Secret 이름 | 용도 | 생성 방법 |
|-------------|------|----------|
| `CLAUDE_TOKEN` | Claude Agent SDK 인증 | `claude login` 후 토큰 추출 → `gh secret set` |
| `GCP_SA_KEY` | BigQuery 접근 (서비스 계정 JSON) | GCP Console에서 키 파일 다운로드 → `gh secret set` |
| `GCP_PROJECT_ID` | BigQuery 프로젝트 식별 | GCP Console에서 프로젝트 ID 확인 → `gh secret set` |
| `GITHUB_PAT` (선택) | PR 생성, 라벨 변경 (PAT 방식) | GitHub Settings → Developer settings → PAT 생성 |

### 4.2 워크플로 내 인증 설정 패턴

```yaml
# .github/workflows/auto-analyze.yml (인증 부분 발췌)
name: 자동 분석 워크플로

on:
  issues:
    types: [labeled]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
      # ── 1단계: 레포 체크아웃 ──
      - name: 레포 체크아웃
        uses: actions/checkout@v4

      # ── 2단계: Claude Code 설치 ──
      - name: Claude Code 설치
        run: |
          npm install -g @anthropic-ai/claude-code
          claude --version

      # ── 3단계: Claude Agent SDK 인증 ──
      - name: Claude Agent SDK 인증
        run: |
          claude setup-token ${{ secrets.CLAUDE_TOKEN }}

      # ── 4단계: GCP 인증 (BigQuery 접근용) ──
      - name: GCP 인증 설정
        run: |
          echo '${{ secrets.GCP_SA_KEY }}' > /tmp/gcp-key.json
          echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json" >> $GITHUB_ENV

      # ── 5단계: Claude Code로 에이전트 실행 ──
      - name: 분석 에이전트 실행
        env:
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          claude -p "이슈 #$ISSUE_NUMBER 의 분석 요청을 처리하세요. AGENTS.md의 워크플로 규약을 따르세요."
```

### 4.3 토큰 유효 기간 및 갱신

| 항목 | 설명 |
|------|------|
| 유효 기간 | Claude Code 인증 토큰은 일정 기간 후 만료될 수 있음 |
| 만료 징후 | 워크플로 실행 시 `401 Unauthorized` 또는 `Authentication failed` 오류 |
| 갱신 방법 | 로컬에서 `claude login` 재실행 → 새 토큰 → `gh secret set CLAUDE_TOKEN` 갱신 |
| 갱신 주기 권장 | 토큰 만료 오류 발생 시 즉시 갱신 (정기 갱신 알림 설정 권장) |

### 4.4 토큰 만료 시 대응 절차

```bash
# 1. 로컬에서 재로그인
claude login

# 2. 새 토큰 확인
claude auth status

# 3. GitHub Secret 갱신
gh secret set CLAUDE_TOKEN --body "<NEW_TOKEN>"

# 4. 실패한 워크플로 재실행
gh run rerun <RUN_ID>
```

---

## 5. CI/CD 환경별 Claude Code 설치

### 5.1 GitHub Actions (Ubuntu 러너)

```yaml
steps:
  - name: Node.js 설정
    uses: actions/setup-node@v4
    with:
      node-version: '20'

  - name: Claude Code 설치
    run: |
      npm install -g @anthropic-ai/claude-code
      claude --version

  - name: Claude Agent SDK 인증
    run: |
      claude setup-token ${{ secrets.CLAUDE_TOKEN }}
```

### 5.2 환경 변수 설정 (전체 예시)

```yaml
env:
  # Claude Code 관련
  CLAUDE_TOKEN: ${{ secrets.CLAUDE_TOKEN }}

  # GCP/BigQuery 관련
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GOOGLE_APPLICATION_CREDENTIALS: /tmp/gcp-key.json

  # GitHub 관련
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # 자동 제공
  ISSUE_NUMBER: ${{ github.event.issue.number }}
```

---

## 6. Claude Code 비대화형 실행 모드

### 6.1 `-p` 플래그 (프롬프트 모드)

CI/CD 환경에서는 **`-p` 플래그**를 사용하여 비대화형으로 Claude Code를 실행합니다:

```bash
# 기본 사용법: 프롬프트를 직접 전달
claude -p "dbt 모델을 작성하세요: DAU 계산 쿼리"

# 파일에서 프롬프트 읽기
claude -p "$(cat prompts/stage-1-parse.md)"

# 환경 변수를 프롬프트에 포함
claude -p "이슈 #${ISSUE_NUMBER}의 분석 요청을 처리하세요."
```

### 6.2 주요 CLI 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-p` | 비대화형 프롬프트 모드 | `claude -p "분석 실행"` |
| `--output-format` | 출력 형식 지정 | `claude -p "..." --output-format json` |
| `--max-turns` | 최대 대화 턴 수 제한 | `claude -p "..." --max-turns 10` |
| `--allowedTools` | 허용할 도구 목록 지정 | `claude -p "..." --allowedTools "Read,Write,Bash"` |

### 6.3 프롬프트 파일 분리 패턴

규모가 큰 프롬프트는 별도 파일로 관리하는 것을 권장합니다:

```
.claude/
├── prompts/
│   ├── stage-1-parse.md        # 단계 1: 이슈 파싱 프롬프트
│   ├── stage-2-define.md       # 단계 2: 문제 정의 프롬프트
│   ├── stage-3-deliverables.md # 단계 3: 산출물 명세 프롬프트
│   ├── stage-4-spec.md         # 단계 4: 스펙 작성 프롬프트
│   ├── stage-5-extract.md      # 단계 5: 데이터 추출 프롬프트
│   ├── stage-6-analyze.md      # 단계 6: 분석 수행 프롬프트
│   └── stage-7-report.md       # 단계 7: 리포트 생성 프롬프트
```

워크플로에서 프롬프트 파일 참조:

```yaml
- name: 에이전트 실행 (단계별 프롬프트)
  run: |
    STAGE=$(echo "$CURRENT_LABEL" | sed 's/stage://')
    PROMPT_FILE=".claude/prompts/${STAGE}.md"

    if [ -f "$PROMPT_FILE" ]; then
      # 프롬프트에 이슈 컨텍스트 주입
      FULL_PROMPT="$(cat $PROMPT_FILE)

      ## 이슈 컨텍스트
      이슈 번호: #${ISSUE_NUMBER}
      이슈 본문:
      ${ISSUE_BODY}

      ## 이전 단계 산출물
      ${PREVIOUS_STAGES}"

      claude -p "$FULL_PROMPT"
    else
      echo "프롬프트 파일을 찾을 수 없음: $PROMPT_FILE"
      exit 1
    fi
```

---

## 7. 보안 모범 사례

### 7.1 토큰 보안 체크리스트

- [ ] **토큰을 코드에 하드코딩하지 않기**: 반드시 GitHub Secret 사용
- [ ] **`.env` 파일을 `.gitignore`에 등록**: 로컬 테스트 시 사용하는 환경 변수 파일이 커밋되지 않도록
- [ ] **최소 권한 원칙**: `permissions:` 블록에서 필요한 권한만 명시
- [ ] **Secret 접근 제한**: 리포지토리 Admin만 Secret을 추가/수정할 수 있도록 설정
- [ ] **워크플로 로그 확인**: `claude setup-token` 실행 시 토큰이 마스킹되는지 확인

### 7.2 Secret 마스킹 검증

GitHub Actions는 Secret 값을 로그에서 자동으로 `***`로 마스킹합니다. 단, 다음 경우 마스킹이 되지 않을 수 있으니 주의하세요:

```yaml
# ❌ 잘못된 예: Secret을 직접 echo
- name: 토큰 확인 (위험!)
  run: echo ${{ secrets.CLAUDE_TOKEN }}

# ✅ 올바른 예: Secret 존재 여부만 확인
- name: 토큰 설정 확인
  run: |
    if [ -z "${{ secrets.CLAUDE_TOKEN }}" ]; then
      echo "⚠️ CLAUDE_TOKEN Secret이 설정되지 않았습니다."
      exit 1
    fi
    echo "✅ CLAUDE_TOKEN이 설정되어 있습니다."
```

### 7.3 GCP 키 파일 정리

워크플로 완료 후 임시 키 파일을 삭제하는 정리 단계를 추가합니다:

```yaml
# 워크플로 마지막 단계에 추가
- name: 임시 인증 파일 정리
  if: always()
  run: |
    rm -f /tmp/gcp-key.json
```

---

## 8. 트러블슈팅

### 8.1 자주 발생하는 오류와 해결법

| 오류 메시지 | 원인 | 해결 방법 |
|------------|------|----------|
| `Authentication failed` | `CLAUDE_TOKEN` 만료 또는 잘못된 토큰 | 로컬에서 `claude login` → 새 토큰으로 Secret 갱신 |
| `command not found: claude` | Claude Code 미설치 | `npm install -g @anthropic-ai/claude-code` 단계 추가 |
| `Permission denied` | GitHub Token 권한 부족 | `permissions:` 블록에 필요한 권한 추가 |
| `Rate limit exceeded` | API 호출 한도 초과 | 워크플로 실행 간격 조절, 불필요한 재실행 방지 |
| `GOOGLE_APPLICATION_CREDENTIALS not set` | GCP 인증 누락 | GCP 인증 설정 단계가 SDK 인증보다 먼저 실행되는지 확인 |

### 8.2 디버깅 방법

```yaml
# 디버그 모드로 워크플로 실행
- name: Claude Code 디버그 실행
  run: |
    # 인증 상태 확인
    claude auth status || echo "인증 실패 - 토큰을 확인하세요"

    # Claude Code 버전 확인
    claude --version

    # 간단한 테스트 프롬프트로 동작 확인
    claude -p "Hello, 현재 시간을 알려주세요." || echo "Claude Code 실행 실패"
```

### 8.3 워크플로 실패 시 재실행

```bash
# 실패한 워크플로 실행 ID 확인
gh run list --status failure --limit 5

# 특정 실행 재실행
gh run rerun <RUN_ID>

# 또는 이슈 라벨로 재트리거
# 실패한 단계의 라벨을 제거 후 다시 부착
gh issue edit <ISSUE_NUMBER> --remove-label "stage:error"
gh issue edit <ISSUE_NUMBER> --add-label "stage:5-extract"  # 실패한 단계 재실행
```

---

## 9. 자기 점검 체크리스트

Claude Agent SDK 설정이 완료되었는지 다음 항목을 확인하세요:

| # | 점검 항목 | 검증 방법 |
|---|----------|----------|
| 1 | Claude Code가 로컬에 설치되어 있다 | `claude --version` 명령이 버전 번호를 출력하는지 확인 |
| 2 | Claude Code에 로그인되어 있다 | `claude whoami` 명령이 사용자 정보를 출력하는지 확인 |
| 3 | `CLAUDE_TOKEN` Secret이 등록되어 있다 | `gh secret list`에서 `CLAUDE_TOKEN`이 표시되는지 확인 |
| 4 | `GCP_SA_KEY` Secret이 등록되어 있다 | `gh secret list`에서 `GCP_SA_KEY`가 표시되는지 확인 |
| 5 | `GCP_PROJECT_ID` Secret이 등록되어 있다 | `gh secret list`에서 `GCP_PROJECT_ID`가 표시되는지 확인 |
| 6 | 테스트 워크플로가 성공적으로 실행된다 | `gh run list --limit 1`로 최근 실행이 `completed`인지 확인 |
| 7 | `claude -p` 비대화형 모드가 동작한다 | 로컬에서 `claude -p "안녕하세요"` 실행 시 응답이 반환되는지 확인 |
| 8 | Secret이 로그에서 마스킹된다 | 워크플로 실행 로그에서 토큰 값이 `***`로 표시되는지 확인 |
