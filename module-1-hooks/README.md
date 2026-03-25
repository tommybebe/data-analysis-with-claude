# 모듈 1: 훅과 설정 엔지니어링

> settings.json으로 에이전트 정책을 구현하는 방법을 배웁니다

**총 학습 시간**: 1.5~2시간

---

## 코스 전체 구조

이 모듈은 **하니스 엔지니어링 for 데이터 분석** 코스의 5개 모듈 중 하나입니다.

| 모듈 | 디렉터리 | 핵심 질문 |
|------|----------|-----------|
| 0 | `module-0-project-setup/` | 에이전트가 작업할 데이터 인프라를 어떻게 구축하는가? |
| **1** | **`module-1-hooks/`** (지금 여기) | **settings.json 훅으로 에이전트 정책을 어떻게 자동 실행하는가?** |
| 2 | `module-2-slash-commands/` | 슬래시 커맨드로 에이전트 작업을 어떻게 명세하는가? |
| 3 | `module-3-orchestration/` | 권한과 워크플로로 에이전트 경계를 어떻게 설계하는가? |
| 4 | `module-4-error-handling/` | 하니스 전체를 통합한 종단간 분석 워크플로를 어떻게 운영하는가? |

> 각 모듈은 독립적으로 실행 가능합니다. 이전 모듈의 산출물은 **사전 구축 파일**로 이 디렉터리에 포함되어 있습니다.

---

## 학습 목표

이 모듈을 완료하면 다음을 **관찰 가능한 행동**으로 증명할 수 있습니다:

1. `.claude/settings.json`을 직접 작성하여 `PreToolUse`, `PostToolUse`, `Stop` 이벤트 훅을 등록하고, JSON 문법 오류 없이 훅 항목이 출력되는 것을 확인할 수 있다
2. BigQuery 비용 가드 훅(`bq-cost-guard.sh`)을 구현하고, 한도를 초과하는 쿼리가 차단되는 것을 터미널 출력으로 캡처할 수 있다
3. `.claude/settings.json`의 `permissions.allow`와 `permissions.deny` 섹션을 설정하고, 위험 명령이 거부되는 것을 확인할 수 있다
4. dbt 모델 파일을 편집한 직후 `PostToolUse` 훅이 `dbt compile`을 자동으로 실행하여 SQL 문법 오류를 즉시 감지하는 것을 시연할 수 있다

---

## 핵심 개념

### 훅 (Hook) — 이벤트 기반 자동 정책 실행

훅(hook)은 Claude Code가 특정 작업을 수행할 때 **자동으로 실행되는 셸 스크립트**입니다. 에이전트에게 규칙을 선언적으로 알려주는 `AGENTS.md`와 달리, 훅은 규칙 위반을 **기계적으로 차단하거나 자동으로 교정**합니다.

| 훅 이벤트 | 트리거 시점 | 용도 예시 |
|-----------|------------|---------|
| `PreToolUse` | 도구(Bash, Edit, Write 등) 실행 **직전** | BigQuery 쿼리 비용 검사, 위험 명령 차단 |
| `PostToolUse` | 도구 실행 **직후** | dbt 컴파일 검증, marimo 문법 검사 |
| `Stop` | Claude Code 세션 **종료 시** | 작업 완료 요약 생성, 증거 파일 저장 |

### 매처 (Matcher) — 어떤 도구·명령에 반응할지 지정

매처(matcher)는 훅이 반응할 이벤트를 좁히는 패턴 문자열입니다:

```json
{ "matcher": "Bash" }                  // 모든 Bash 실행 — 너무 넓음
{ "matcher": "Bash(bq query*)" }       // bq query로 시작하는 명령만 — 적절
{ "matcher": "Edit(models/**/*.sql)" } // models/ 아래 SQL 파일 편집만 — 적절
```

### settings.json 구조 — 두 가지 핵심 섹션

`.claude/settings.json`은 두 가지 하니스 설정을 담습니다:

```json
{
  "permissions": {
    "allow": ["Bash(dbt run:*)", "Read", "Write", "Edit"],
    "deny":  ["Bash(git push --force:*)", "Bash(bq rm:*)"]
  },
  "hooks": {
    "PreToolUse": [{ "matcher": "Bash", "hooks": [{"type": "command", "command": "..."}] }],
    "PostToolUse": [{ "matcher": "Edit", "hooks": [{"type": "command", "command": "..."}] }],
    "Stop": [{ "hooks": [{"type": "command", "command": "..."}] }]
  }
}
```

- **`permissions`**: Claude Code가 실행할 수 있는 명령의 허용/거부 목록 (정적 ACL)
- **`hooks`**: 이벤트 발생 시 동적으로 실행되는 스크립트 체인

### 훅 스크립트 종료 코드

- **exit 0**: 작업 허용 / 훅 성공 — Claude Code가 계속 진행
- **exit 1**: 작업 차단 / 훅 실패 — Claude Code가 해당 작업을 중단
- `PreToolUse` 훅에서 `exit 1` → 도구 실행 자체가 **취소됨**
- `PostToolUse` 훅에서 `exit 1` → 실행은 완료되었지만 **오류 보고**

### permissions vs hooks 선택 기준

| 관점 | `permissions.deny` | `PreToolUse` 훅 |
|------|-------------------|-----------------|
| 평가 시점 | 패턴 매칭으로 **즉시** 거부 | 도구 실행 **직전**에 스크립트 실행 |
| 동적 검사 | ❌ 불가능 (정적 패턴) | ✅ 가능 (런타임 값 검사) |
| 적합 사례 | `git push --force`, `bq rm` | BigQuery 비용 계산 (dry-run 필요) |

---

## 사전 구축 파일 vs 학습자 생성 파일

### 사전 구축 파일 (이 디렉터리에 포함)

작동하는 데이터 파이프라인이 **사전 구축(frozen) 파일**로 포함되어 있습니다:

| 파일 | 설명 | 출처 |
|------|------|------|
| `dbt_project.yml` | dbt 프로젝트 설정 | 사전 구축 |
| `packages.yml` | dbt 패키지 의존성 | 사전 구축 |
| `models/staging/sources.yml` | BigQuery 소스 선언 | 사전 구축 |
| `models/staging/stg_events.sql` | 이벤트 정제 모델 | 사전 구축 |
| `models/staging/stg_users.sql` | 사용자 프로필 모델 | 사전 구축 |
| `models/marts/fct_daily_active_users.sql` | DAU 집계 | 사전 구축 |
| `models/marts/fct_monthly_active_users.sql` | MAU 집계 | 사전 구축 |
| `models/marts/fct_retention_cohort.sql` | 코호트 리텐션 | 사전 구축 |
| `models/staging/schema.yml` | 스테이징 테스트 | 사전 구축 |
| `models/marts/schema.yml` | 마트 테스트 | 사전 구축 |
| `scripts/generate_synthetic_data.py` | 합성 데이터 생성 | 사전 구축 |
| `scripts/load_to_bigquery.py` | BigQuery 로딩 | 사전 구축 |
| `AGENTS.md` | 에이전트 규칙 선언 | 사전 구축 |
| `pyproject.toml` | Python 의존성 | 이 모듈 제공 |
| `CLAUDE.md` | 에이전트 지시 파일 | 이 모듈 제공 |
| `.env.example` | 환경 변수 템플릿 | 이 모듈 제공 |
| `.claude/commands/validate.md` | 검증 커맨드 | 이 모듈 제공 |

### 학습자가 직접 생성하는 파일

다음 파일은 이 모듈에서 학습자가 직접 작성합니다:

| 파일 | 설명 | 분류 |
|------|------|------|
| `.claude/settings.json` | 훅 + 권한 설정 (hooks, permissions) | 하니스 설정 |
| `.claude/hooks/bq-cost-guard.sh` | PreToolUse — BigQuery 비용 가드 | 하니스 설정 |
| `.claude/hooks/dbt-auto-test.sh` | PostToolUse — dbt 컴파일 검증 | 하니스 설정 |
| `.claude/hooks/stop-summary.sh` | Stop — 세션 요약 생성 | 하니스 설정 |
| `evidence/module-1-retrospective.md` | 훅 설계 회고 기록 | 하니스 효과 측정 |
| `evidence/session_log.json` | Stop 훅이 자동 생성 | 파이프라인 산출물 |

---

## 시작하기

### 사전 준비

이 모듈을 시작하기 전에 다음이 준비되어 있어야 합니다:

- Python 3.11+, uv 패키지 매니저 설치
- Claude Code CLI 설치 및 인증 완료 (`claude whoami`)
- GCP 프로젝트 및 서비스 계정 키 파일 준비
- BigQuery에 합성 데이터 로딩 완료 (raw_events ~500k행, raw_users ~10k행)
- dbt 파이프라인 정상 동작 확인 (`uv run dbt run && uv run dbt test`)

> 이 디렉터리에는 dbt 모델, 스크립트 등 데이터 인프라 파일이 **사전 구축(frozen)** 상태로 포함되어 있습니다. 환경 설정(uv, dbt, GCP)과 BigQuery 데이터 로딩만 완료하면 바로 시작할 수 있습니다.

### 환경 설정

```bash
# 1. 디렉터리 이동 및 Claude Code 실행
cd module-1-hooks
claude

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 GCP_PROJECT_ID와 GOOGLE_APPLICATION_CREDENTIALS 입력

# 3. Python 의존성 설치
uv sync

# 4. dbt 패키지 설치
uv run dbt deps

# 5. dbt 프로필 설정 (아직 없다면)
cp profiles.yml.example profiles.yml
# profiles.yml의 실제 경로와 프로젝트 ID를 수정

# 6. 파이프라인 정상 동작 확인
uv run dbt debug
uv run dbt run
uv run dbt test
```

---

## 활동

### 활동 1: settings.json 구조 탐색 및 첫 번째 훅 등록 *(15~20분)*

> **하니스 설정**: `.claude/settings.json`과 그 안에 등록하는 훅 스크립트는 순수한 **하니스 설정**입니다.

```bash
# .claude 디렉토리에 hooks 하위 폴더 생성
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

# JSON 문법 검증
cat .claude/settings.json | python -m json.tool
```

가장 간단한 훅부터 등록합니다 — `Stop` 이벤트에 세션 종료 요약을 출력하는 훅:

```bash
# Stop 훅 스크립트 생성
cat > .claude/hooks/stop-summary.sh << 'EOF'
#!/usr/bin/env bash
# stop-summary.sh — Session end summary output
# Hook type: Stop
# Role: Improve observability — log what the agent did

echo "=== 세션 완료 요약 ===" >&2
echo "종료 시각: $(date '+%Y-%m-%d %H:%M:%S')" >&2
echo "최근 수정 파일:" >&2
git diff --name-only HEAD 2>/dev/null | head -10 >&2 || echo "  (git 변경 없음)" >&2
exit 0
EOF
chmod +x .claude/hooks/stop-summary.sh
```

`settings.json`에 Stop 훅을 등록한 후 Claude Code를 실행하여 동작을 확인하세요.

### 활동 2: PreToolUse 훅 — BigQuery 비용 가드 구현 *(25~30분)*

> **비용 의식**: BigQuery on-demand 가격은 $5/TB입니다. 에이전트가 반복 실행할 수 있으므로 훅으로 자동 차단이 필수입니다.

`.claude/hooks/bq-cost-guard.sh`를 생성합니다:
- PreToolUse 훅으로 Bash 매처에 등록
- STDIN으로 전달되는 JSON에서 `tool_input.command` 추출
- `bq query` 명령이면 dry-run으로 예상 스캔 바이트 확인
- `BQ_COST_LIMIT_BYTES` (기본 1GB) 초과 시 `exit 1`로 차단

**차단 동작 테스트**:
```bash
# 임계값을 1바이트로 낮춰 차단 강제 테스트
export BQ_COST_LIMIT_BYTES=1
echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' \
  | bash .claude/hooks/bq-cost-guard.sh
echo "훅 종료 코드: $?"  # 1이어야 함
unset BQ_COST_LIMIT_BYTES
```

### 활동 3: PostToolUse 훅 — dbt 자동 컴파일 검증 *(20~25분)*

`.claude/hooks/dbt-auto-test.sh`를 생성합니다:
- PostToolUse 훅으로 Write/Edit 매처에 등록
- `models/**/*.sql` 파일 변경 시 `dbt compile` 자동 실행
- 컴파일 실패 시 `exit 1`로 오류 보고

**의도적 실패 테스트**:
```bash
echo "SELEC * FORM broken_table" > models/marts/test_broken.sql
echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/test_broken.sql"}}' \
  | bash .claude/hooks/dbt-auto-test.sh
rm models/marts/test_broken.sql
```

### 활동 4: permissions.allow / permissions.deny 정책 설정 *(15~20분)*

`settings.json`에 permissions 섹션을 추가합니다:

**allow 예시**: `dbt run/test/compile`, `bq query --dry_run`, `git status/log/diff`, `Read`, `Write`, `Edit`

**deny 예시**: `git push --force`, `bq rm`, `dbt run --full-refresh`, `rm -rf`

> **설계 원칙**: `deny`는 최소한으로 유지하고 구체적 패턴을 사용합니다. 너무 넓은 deny는 에이전트를 무력화합니다.

### 활동 5: Stop 훅 업그레이드 — 작업 완료 요약 생성 *(15~20분)*

Stop 훅을 업그레이드하여 분석 세션의 작업 요약을 `evidence/session_log.json`에 JSON 형식으로 저장합니다.

### 활동 6: 훅 의도적 실패 테스트 및 디버깅 *(15~20분)*

훅 엔지니어링의 핵심 역량은 **의도적으로 실패시키고 디버깅하는 것**입니다:

1. **JSON 문법 오류 주입**: settings.json에 의도적 오류 → 파싱 실패 확인
2. **실행 권한 누락**: `chmod -x` 후 훅 미실행 확인 → `chmod +x`로 복구
3. **매처 범위 테스트**: 넓은/좁은 매처의 false positive/negative 관찰

```bash
# 전체 설정 최종 검증
echo "=== settings.json 검증 ===" && python -m json.tool .claude/settings.json && echo "✅ JSON 정상"
echo "=== 훅 스크립트 권한 확인 ===" && ls -la .claude/hooks/*.sh
```

---

## Claude Code 프롬프트 예제

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
1. .claude/hooks/bq-cost-guard.sh — PreToolUse, Bash 매처, dry-run 비용 확인
2. .claude/hooks/dbt-auto-test.sh — PostToolUse, Write/Edit 매처, dbt compile 검증
3. .claude/hooks/stop-summary.sh — Stop 이벤트, 세션 요약 evidence/ 저장
각 스크립트 생성 후 chmod +x 실행."
```

---

## 관찰-수정-창작 사이클

### 관찰 (observe)

훅 설정 전후로 동일한 에이전트 작업을 실행하여 차이를 관찰합니다:

- 훅 없는 상태: 에이전트가 비용이 큰 쿼리를 경고 없이 실행
- 훅 등록 후: bq query 실행 시 비용 가드 작동, SQL 편집 시 자동 검증, 세션 종료 시 요약 생성

### 회고 질문

아래 질문에 대한 답변을 `evidence/module-1-retrospective.md`에 기록하세요.

**영역 A: 훅 동작 검증**

1. **비용 가드 차단 테스트 결과**: `BQ_COST_LIMIT_BYTES=1`로 설정하여 강제 차단을 테스트했을 때 어떤 메시지가 출력되었는가?
2. **의도적 실패 케이스**: 훅 스크립트를 의도적으로 실패시키는 방법을 3가지 나열하라.

**영역 B: 정책 설계 판단**

3. **매처 범위 트레이드오프**: `PreToolUse` 훅의 매처를 `"Bash"` vs `"Bash(bq query*)"` 로 설정했을 때의 false positive와 false negative는?
4. **permissions vs hooks 선택 기준**: `git push --force`를 차단할 때 `permissions.deny` vs `PreToolUse` 훅 — 어느 것이 더 나은가?

**영역 C: 하니스 정합성**

5. **AGENTS.md와 settings.json 정합성**: `AGENTS.md`의 "1GB 한도"와 `bq-cost-guard.sh`의 `BQ_COST_LIMIT_BYTES` 기본값이 일치하는지 확인하라.

### 창작 (create)

회고 결과를 바탕으로:
1. false positive가 발생한 훅의 매처 패턴을 좁혀 수정
2. `.claude/thresholds.env`에 임계값을 정의하고 훅 스크립트에서 `source`로 로드하는 구조로 리팩토링
3. `python -m json.tool .claude/settings.json`을 pre-commit 훅에 포함하여 JSON 문법 자동 검증

---

## 완료 체크리스트

> 6개 항목 **모두 합격**이어야 이 모듈을 완료한 것입니다.

### 기대 산출물 요약

| # | 산출물 | 위치/형태 | 분류 |
|---|--------|-----------|------|
| 1 | `.claude/settings.json` | JSON 문법 정상, hooks + permissions 섹션 포함 | 하니스 설정 |
| 2 | `bq-cost-guard.sh` | `.claude/hooks/` — 실행 권한, PreToolUse + Bash 매처 | 하니스 설정 |
| 3 | `dbt-auto-test.sh` | `.claude/hooks/` — 실행 권한, PostToolUse + Write/Edit 매처 | 하니스 설정 |
| 4 | `stop-summary.sh` | `.claude/hooks/` — 실행 권한, Stop 이벤트 | 하니스 설정 |
| 5 | `session_log.json` | `evidence/` — Stop 훅 실행 후 자동 생성 | 파이프라인 산출물 |
| 6 | 회고 기록 | `evidence/module-1-retrospective.md` | 하니스 효과 측정 |

### 자가 점검

**[점검 1/6]** settings.json 존재 및 JSON 문법 정상
```bash
cat .claude/settings.json | python -m json.tool
# ✅ 합격: "hooks"와 "permissions" 키 모두 존재
```

**[점검 2/6]** 훅 스크립트 실행 권한
```bash
ls -la .claude/hooks/*.sh
# ✅ 합격: 3개 파일 모두 실행 비트(x) 설정됨
```

**[점검 3/6]** 비용 가드 차단 동작
```bash
export BQ_COST_LIMIT_BYTES=1
echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' \
  | bash .claude/hooks/bq-cost-guard.sh
echo "exit: $?"  # 1이어야 함
unset BQ_COST_LIMIT_BYTES
```

**[점검 4/6]** dbt 오류 감지
```bash
echo "SELEC * FORM broken" > models/marts/test_broken.sql
echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/test_broken.sql"}}' \
  | bash .claude/hooks/dbt-auto-test.sh
echo "exit: $?"  # 1이어야 함
rm models/marts/test_broken.sql
```

**[점검 5/6]** permissions.deny 차단 설정
```bash
python -m json.tool .claude/settings.json | grep -A 10 '"deny"'
# ✅ 합격: git push --force, bq rm, dbt run --full-refresh, rm -rf 포함
```

**[점검 6/6]** 핵심 개념 이해
```bash
cat evidence/module-1-retrospective.md
# ✅ 합격: permissions vs hooks 차이 설명 포함
```

---

## 완료 확인

> `/validate` 명령으로 모듈 완료 상태를 확인할 수 있습니다.
