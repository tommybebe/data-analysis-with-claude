# 학습 사이클 워크스루: 모듈 2 — DAU/MAU 분석으로 스킬과 훅 구축하기

> 이 문서는 모듈 2(스킬과 훅)에서 **관찰(observe) → 수정(modify) → 창작(create)** 3단계 학습 사이클이 구체적으로 어떻게 진행되는지를 보여주는 end-to-end 워크스루입니다.
>
> FitTrack 모바일 앱의 DAU/MAU 분석 시나리오를 사용하며, 각 단계에서 실행하는 Claude Code 명령, 생성되는 파일, 관찰할 포인트를 구체적으로 기술합니다.

---

## 사전 조건

모듈 1을 완료한 상태로, 다음 파일이 레포에 존재해야 합니다:

```
✅ AGENTS.md                        — 에이전트 컨텍스트 (모듈 1 산출물)
✅ models/staging/sources.yml       — 데이터 계약 포함
✅ models/staging/stg_events.sql    — 이벤트 스테이징 모델
✅ models/staging/stg_users.sql     — 사용자 스테이징 모델
✅ models/marts/fct_daily_active_users.sql  — DAU 마트 모델 (스타터 제공)
✅ models/marts/fct_monthly_active_users.sql — MAU 마트 모델 (스타터 제공)
✅ .github/ISSUE_TEMPLATE/analysis-request.yml — 이슈 템플릿 (모듈 1 산출물)
```

`.claude/` 디렉토리는 **아직 없는 상태**입니다 — 이것이 모듈 2의 핵심 산출물입니다.

---

## Phase 1: 관찰 (약 40분)

### 목표

스킬과 훅이 없는 상태에서 Claude Code로 DAU/MAU 분석을 수행하며, 에이전트의 **정책 미준수**와 **피드백 부재** 문제를 직접 관찰합니다.

### 관찰 1-1: 스킬 없이 DAU 분석 요청

터미널에서 Claude Code를 실행합니다:

```bash
claude
```

대화형 모드에서 다음 프롬프트를 입력합니다:

```
FitTrack 앱의 2026년 1월 DAU를 플랫폼(iOS/Android)별로 일별 집계해줘.
결과를 marimo 노트북으로 만들어서 라인 차트로 시각화해줘.
```

#### 관찰할 행동

에이전트의 응답과 행동을 주의 깊게 관찰하고 기록합니다:

| 관찰 항목 | 확인 질문 | 기록할 내용 |
|-----------|-----------|-------------|
| **데이터 접근** | 에이전트가 `fct_daily_active_users` 마트를 사용하는가, 아니면 새로운 쿼리를 작성하는가? | 실제 참조한 테이블/모델명 |
| **비용 확인** | BigQuery 쿼리 실행 전 `--dry_run`을 수행하는가? | dry-run 수행 여부 (예/아니오) |
| **노트북 규약** | marimo 노트북의 차트 제목이 한국어인가? 파일 경로가 `notebooks/` 아래인가? | 파일 경로, 차트 언어 |
| **검증 행위** | 분석 완료 후 dbt test를 실행하는가? 결과에 대한 sanity check를 하는가? | 검증 단계 수행 여부 |

#### 예상되는 문제 (관찰 노트)

```markdown
## 관찰 1-1 노트

### 프롬프트
"FitTrack 앱의 2026년 1월 DAU를 플랫폼별로 일별 집계해줘..."

### 에이전트 행동
1. ✅ `fct_daily_active_users` 마트 모델을 참조함 (AGENTS.md 효과)
2. ❌ BigQuery 쿼리 실행 전 dry-run을 수행하지 않음
3. ❌ marimo 노트북 파일을 `analysis.py`로 생성 — 규약 경로(`notebooks/analysis_<N>.py`) 미준수
4. ❌ 차트 축 레이블이 영어("Date", "DAU")
5. ❌ 분석 완료 후 dbt test 미실행
6. ❌ 완료 증거(evidence) 없이 텍스트로 "완료했습니다" 보고
```

### 관찰 1-2: 비용 위반 시나리오

다음 프롬프트로 의도적으로 넓은 범위의 쿼리를 요청합니다:

```
2025년 전체의 모든 이벤트를 raw_events 테이블에서 직접 조회해서
사용자별 총 이벤트 수를 계산해줘. SELECT * 로 전체 데이터를 먼저 확인하고 싶어.
```

#### 관찰할 행동

| 관찰 항목 | 확인 질문 |
|-----------|-----------|
| **정책 위반** | `SELECT *` 금지 규칙이 AGENTS.md에 있는데 에이전트가 이를 따르는가? |
| **비용 제어** | 대용량 스캔이 예상되는 쿼리를 차단하는 메커니즘이 있는가? |
| **raw 테이블 접근** | `AGENTS.md`의 "raw 테이블 직접 쿼리 지양" 규칙을 따르는가? |

#### 예상되는 문제

```markdown
## 관찰 1-2 노트

### 프롬프트
"2025년 전체의 모든 이벤트를 raw_events에서 직접 조회..."

### 에이전트 행동
1. ⚠️ AGENTS.md에 SELECT * 금지가 있지만, 사용자가 명시적으로 요청하여 에이전트가 따를 수도 있음
2. ❌ dry-run으로 스캔 바이트를 미리 확인하는 과정이 없음
3. ❌ 1GB 초과 쿼리를 자동으로 차단하는 메커니즘 부재
4. ⚠️ AGENTS.md의 규칙은 "기대"일 뿐, 강제(enforce) 수단이 없음

### 핵심 관찰
→ 선언적 규칙(AGENTS.md)만으로는 정책을 보장할 수 없다.
→ 실행적 보장(훅)이 필요하다.
```

### Phase 1 완료 기준

다음을 모두 만족하면 Phase 2로 진행합니다:

- [x] 최소 2회의 에이전트 작업 실행 완료 (관찰 1-1, 1-2)
- [x] 각 실행에서 에이전트의 구체적 행동(실행 명령, 생성 파일, 출력 내용)을 기록
- [x] 성공 행동(마트 모델 참조)과 실패 행동(dry-run 미수행)을 모두 관찰

---

## Phase 2: 수정 (약 30분)

### 목표

Phase 1에서 관찰한 문제를 분석하고, **스킬과 훅으로 해결할 수 있는 구체적 문제 목록**을 도출하며 기존 컴포넌트를 수정합니다.

### 수정 질문에 답변하기

모듈 2의 수정 단계 질문에 대해 서면으로 답변을 작성합니다.

#### 질문 1: 행동 관찰

> "에이전트에게 DAU 분석을 요청했을 때, 예상과 달랐던 행동은 무엇인가?"

**답변 예시**:

```markdown
1. **dry-run 미수행**: AGENTS.md에 "쿼리 실행 전 dry-run 필수"라고 명시했지만,
   에이전트는 이를 무시하고 바로 쿼리를 실행했다. 선언적 규칙만으로는
   비용 제어가 보장되지 않는다.

2. **노트북 파일 경로 불일치**: `notebooks/analysis_<N>.py` 형식 대신
   프로젝트 루트에 `analysis.py`를 생성했다. 네이밍 규약 위반.

3. **시각화 언어 불일치**: 차트 제목과 축 레이블이 영어로 생성됨.
   AGENTS.md에 "한국어" 규칙이 있지만 에이전트가 일관되게 따르지 않음.

4. **완료 보고의 모호성**: "분석을 완료했습니다"라는 텍스트만 출력.
   dbt 테스트 결과, 쿼리 비용, 생성된 파일 경로 등의 기계적 증거가 없음.
```

#### 질문 2: 위험 평가

> "이 행동이 프로덕션 환경에서 자동으로 실행되면 어떤 결과를 초래하는가?"

**답변 예시**:

```markdown
1. **비용 폭주**: dry-run 없이 대용량 쿼리가 실행되면 BigQuery 비용이
   예상치를 크게 초과할 수 있음. 특히 자동 파이프라인에서는 사람이
   중간에 확인할 수 없어 위험이 증폭됨.

2. **재현 불가능한 분석**: 파일 경로가 일관되지 않으면 후속 단계
   (리포트 생성, PR 포함)에서 파일을 찾지 못해 파이프라인이 실패.

3. **검증 없는 결과 배포**: dbt test 없이 생성된 분석 결과가 PR로
   머지되면, 잘못된 데이터에 기반한 비즈니스 의사결정으로 이어질 수 있음.
```

#### 질문 3: 원인 분석 — 스킬 vs 훅 매핑

> "각 문제의 원인은 컨텍스트 부족 / 정책 부재 / 피드백 부재 중 어디에 해당하며, 스킬과 훅 중 어떤 컴포넌트로 해결하는 것이 적절한가?"

**답변 예시 — 문제-컴포넌트 매핑 표**:

| # | 관찰된 문제 | 원인 분류 | 해결 컴포넌트 | 구현 방법 |
|---|------------|-----------|---------------|-----------|
| 1 | dry-run 미수행 | 피드백 부재 | **훅** | 쿼리 실행 전 자동 dry-run + 바이트 한도 체크 |
| 2 | 노트북 경로/네이밍 위반 | 정책 부재 | **스킬** | `/analyze` 스킬에 파일 경로 생성 로직 내장 |
| 3 | 차트 언어 불일치 | 컨텍스트 부족 | **스킬** | `/analyze` 스킬 프롬프트에 시각화 규약 명시 |
| 4 | dbt test 미실행 | 피드백 부재 | **훅** | 커밋 전 자동 `dbt test` 실행 훅 |
| 5 | 완료 증거 부재 | 정책 부재 | **스킬** | 스킬 출력 형식에 증거 JSON 포함 의무화 |
| 6 | 대용량 쿼리 미차단 | 피드백 부재 | **훅** | BigQuery 비용 가드 훅 (1GB 초과 시 차단) |

#### 질문 4: 해결 설계

> "스킬과 훅 중, 어떤 것이 에이전트의 실수를 더 효과적으로 방지하는가? 그 이유는?"

**답변 예시**:

```markdown
**훅이 더 효과적**이다. 이유:

- 스킬은 에이전트가 "호출하기로 결정"해야 작동한다.
  에이전트가 스킬을 무시하고 직접 쿼리를 실행할 수 있다.
- 훅은 이벤트 기반으로 "자동 실행"된다.
  에이전트의 결정과 무관하게 정책이 강제된다.

하지만 스킬도 중요하다:
- 복잡한 멀티스텝 작업을 일관된 절차로 캡슐화
- 에이전트가 "올바른 방법"을 쉽게 선택할 수 있는 경로 제공

결론: 스킬로 "올바른 경로"를 제공하고, 훅으로 "위험한 경로"를 차단하는
이중 방어(defense in depth)가 최적.
```

### Phase 2 완료 기준

- [x] 모듈 2 수정 질문 4개에 대한 서면 답변 완료
- [x] 최소 4건의 문제를 스킬/훅 컴포넌트 유형에 매핑
- [x] 각 매핑에 구체적 구현 방법 기술

---

## Phase 3: 창작 (약 50분)

### 목표

Phase 2에서 도출한 문제-컴포넌트 매핑을 바탕으로, **새로운 스킬 파일과 훅 설정**을 처음부터 구현하고 효과를 검증합니다.

### 3-1: `/analyze` 스킬 생성

Claude Code에서 다음 프롬프트를 실행합니다:

```bash
claude "/analyze 스킬을 만들어줘. .claude/commands/analyze.md 파일을 생성해.
이슈에서 분석 요청을 파싱하여 dbt 쿼리 확인 + marimo 노트북 생성을 수행하는 스킬이야.
다음 규칙을 반드시 포함해줘:
1. marimo 노트북 경로: notebooks/analysis_<이슈번호>.py
2. 차트 제목/축 레이블: 한국어
3. 첫 번째 셀: 분석 요약, 마지막 셀: 결론 및 제안
4. BigQuery 쿼리 전 dry-run으로 비용 확인
5. 완료 시 evidence/ 디렉토리에 증거 JSON 생성"
```

#### 기대 산출물: `.claude/commands/analyze.md`

```markdown
# 분석 실행

GitHub Issue에서 분석 요청을 파싱하여 dbt 쿼리와 marimo 노트북을 생성합니다.

## 입력
- $ARGUMENTS: 분석 요청 내용 (Issue 본문 또는 직접 입력)

## 실행 단계
1. 입력에서 문제 정의, 기대 산출물, 데이터 범위, 세그먼트를 추출
2. AGENTS.md의 dbt 규약에 따라 필요한 dbt 모델/쿼리 확인
3. 기존 mart 모델(fct_daily_active_users, fct_monthly_active_users)로 충분한지 판단
4. 필요 시 추가 dbt 모델 작성 (staging → mart 레이어 규약 준수)
5. marimo 노트북 생성 (notebooks/analysis_<이슈번호>.py)
6. 노트북에서 데이터 조회, 분석, 시각화 로직 구현
7. 완료 증거 생성 (evidence/ 디렉토리)

## 노트북 규약
- 파일 경로: `notebooks/analysis_<이슈번호>.py`
- 첫 번째 셀: 분석 제목, 기간, 핵심 발견 요약 (한국어)
- 차트 제목, 축 레이블, 범례: **한국어**
- 색상: 일관된 팔레트 (plotly 기본)
- 숫자 포맷: 천 단위 쉼표, 비율 소수점 2자리
- 마지막 셀: 결론 및 제안 사항 (한국어)

## BigQuery 비용 확인
- 쿼리 실행 전 반드시 `bq query --dry_run`으로 스캔 바이트 확인
- 단일 쿼리 스캔 1GB 초과 시 사용자에게 확인 요청
- `SELECT *` 사용 금지

## 출력
- dbt 모델 파일 (필요 시)
- marimo 노트북 파일 (.py)
- 완료 증거 JSON (`evidence/analysis_<이슈번호>.json`)

## 완료 증거 형식
evidence/ 디렉토리에 다음 구조의 JSON을 생성:
```json
{
  "analysis_id": "<이슈번호>",
  "timestamp": "<ISO 8601>",
  "dbt_test_result": { "passed": N, "failed": 0, "total": N },
  "query_cost": { "total_bytes_scanned": N, "limit_bytes": 1073741824 },
  "generated_files": ["notebooks/analysis_<N>.py"],
  "chart_language": "ko"
}
```

## 제약 조건
- AGENTS.md의 모든 규약 준수
- raw 테이블 직접 쿼리 금지 — 반드시 dbt mart/staging 모델 사용
```

#### 검증 명령

스킬이 제대로 등록되었는지 확인합니다:

```bash
# 파일 존재 확인
ls -la .claude/commands/analyze.md

# Claude Code에서 스킬 호출 테스트
claude "/analyze FitTrack 앱의 2026년 1월 DAU를 플랫폼별로 집계하고 라인 차트로 시각화해줘"
```

### 3-2: `/validate-models` 스킬 생성

```bash
claude ".claude/commands/validate-models.md 파일을 만들어줘.
dbt run + dbt test를 실행하고 결과를 요약하는 스킬이야.
테스트 결과를 JSON 형식으로 evidence/ 디렉토리에도 저장해줘."
```

#### 기대 산출물: `.claude/commands/validate-models.md`

```markdown
# dbt 모델 검증

dbt run과 dbt test를 실행하고 결과를 요약합니다.

## 입력
- $ARGUMENTS: 검증 대상 (비워두면 전체 모델, 특정 모델명 지정 가능)

## 실행 단계
1. `dbt run` 실행 (대상 모델 빌드)
2. `dbt test` 실행 (데이터 품질 검증)
3. 결과 요약 출력 (성공/실패 모델 수, 실패한 테스트 상세)
4. 결과 JSON을 `evidence/dbt_validation.json`에 저장

## 출력 형식
### 성공 시:
✅ dbt 검증 완료
- 모델 빌드: N개 성공 / 0개 실패
- 테스트: N개 통과 / 0개 실패
- 증거 파일: evidence/dbt_validation.json

### 실패 시:
❌ dbt 검증 실패
- 실패 모델: [모델명 목록]
- 실패 테스트: [테스트명 + 에러 메시지]
- 권장 조치: [수정 가이드]
```

### 3-3: BigQuery 비용 가드 훅 생성

`.claude/settings.json` 파일을 생성하여 훅을 등록합니다:

```bash
claude ".claude/settings.json 파일을 만들어줘. 다음 훅을 설정해줘:
1. PreToolUse 훅: Bash 도구로 bq query 실행 시 자동으로 --dry_run 비용 체크.
   스캔 바이트가 1GB 초과하면 경고 출력하고 차단.
2. PostToolUse 훅: .sql 파일 저장 시 기본 SQL lint 검사 수행.
AGENTS.md의 BigQuery 정책을 강제하는 훅이야."
```

#### 기대 산출물: `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(dbt *)",
      "Bash(bq query --dry_run *)",
      "Bash(marimo *)",
      "Read(*)",
      "Write(models/**)",
      "Write(notebooks/**)",
      "Write(evidence/**)"
    ],
    "deny": [
      "Bash(bq query * --no-dry-run *)",
      "Bash(* DELETE *)",
      "Bash(* DROP *)",
      "Bash(* TRUNCATE *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(bq query*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/bq-cost-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write(models/**/*.sql)",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/dbt-auto-test.sh"
          }
        ]
      }
    ]
  }
}
```

### 3-4: 훅 스크립트 생성

```bash
claude ".claude/hooks/bq-cost-guard.sh 스크립트를 만들어줘.
stdin으로 전달되는 tool_input에서 SQL 쿼리를 추출하고,
bq query --dry_run으로 예상 스캔 바이트를 확인해서
1GB(1073741824 바이트) 초과 시 exit 2로 차단하는 스크립트야.
결과를 JSON으로 evidence/cost_check.json에도 기록해줘."
```

#### 기대 산출물: `.claude/hooks/bq-cost-guard.sh`

```bash
#!/bin/bash
# bq-cost-guard.sh — BigQuery 쿼리 비용 가드 훅
# PreToolUse 훅으로 실행되며, 스캔 바이트 1GB 초과 시 쿼리를 차단합니다.

set -euo pipefail

LIMIT_BYTES=1073741824  # 1 GB

# stdin에서 tool input 읽기
INPUT=$(cat)
QUERY=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)

# bq query 명령이 아니면 패스
if [[ ! "$QUERY" =~ "bq query" ]]; then
  exit 0
fi

# SQL 추출 (간단 버전)
SQL=$(echo "$QUERY" | sed 's/.*bq query//' | sed 's/--[^ ]* [^ ]*//g')

# dry-run 실행
RESULT=$(bq query --dry_run --use_legacy_sql=false "$SQL" 2>&1)
BYTES=$(echo "$RESULT" | grep -oP '\d+' | head -1)

# 비용 기록
mkdir -p evidence
cat > evidence/cost_check.json <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "query_preview": "$(echo "$SQL" | head -c 200)",
  "estimated_bytes": ${BYTES:-0},
  "limit_bytes": $LIMIT_BYTES,
  "allowed": $([ "${BYTES:-0}" -le "$LIMIT_BYTES" ] && echo "true" || echo "false")
}
EOF

# 한도 초과 시 차단
if [ "${BYTES:-0}" -gt "$LIMIT_BYTES" ]; then
  echo "❌ 비용 가드: 예상 스캔 $(numfmt --to=iec ${BYTES})가 한도 1GB를 초과합니다."
  echo "   쿼리를 최적화하거나 WHERE 조건을 추가하세요."
  exit 2  # exit 2 = 훅에서 도구 실행 차단
fi

echo "✅ 비용 가드: 예상 스캔 $(numfmt --to=iec ${BYTES:-0}) (한도 1GB 이내)"
exit 0
```

### 3-5: before/after 비교 — 동일 프롬프트 재실행

Phase 1과 **동일한 프롬프트**를 다시 실행하여 행동 변화를 확인합니다.

#### 재실행 1: `/analyze` 스킬로 DAU 분석

```bash
claude "/analyze FitTrack 앱의 2026년 1월 DAU를 플랫폼(iOS/Android)별로 일별 집계해줘. 결과를 marimo 노트북으로 만들어서 라인 차트로 시각화해줘."
```

#### before/after 비교 기록

| # | 관찰 항목 | Phase 1 (before) | Phase 3 (after) | 변화 |
|---|-----------|------------------|-----------------|------|
| 1 | 데이터 접근 | `fct_daily_active_users` 사용 ✅ | `fct_daily_active_users` 사용 ✅ | 유지 (AGENTS.md 효과) |
| 2 | dry-run 수행 | 미수행 ❌ | 비용 가드 훅이 자동 실행 ✅ | **개선** — 훅이 강제 |
| 3 | 노트북 경로 | `./analysis.py` ❌ | `notebooks/analysis_1.py` ✅ | **개선** — 스킬이 경로 규약 내장 |
| 4 | 차트 언어 | 영어 ❌ | 한국어 ✅ | **개선** — 스킬에 시각화 규약 명시 |
| 5 | dbt test | 미실행 ❌ | SQL 저장 시 자동 실행 ✅ | **개선** — 훅이 자동 트리거 |
| 6 | 완료 증거 | 텍스트 보고만 ❌ | `evidence/analysis_1.json` 생성 ✅ | **개선** — 스킬이 증거 생성 의무화 |

#### 재실행 2: 비용 초과 쿼리 차단 확인

```bash
claude "raw_events 테이블에서 SELECT * 로 2025년 전체 이벤트를 조회해줘."
```

**기대 결과**: 비용 가드 훅이 dry-run을 실행하고, 1GB 초과 시 차단 메시지를 출력합니다.

```
❌ 비용 가드: 예상 스캔 2.3G가 한도 1GB를 초과합니다.
   쿼리를 최적화하거나 WHERE 조건을 추가하세요.
```

### Phase 3 산출물 정리

모든 작업 후 레포에 추가된 파일을 확인합니다:

```bash
# 생성된 파일 목록 확인
find .claude -type f | sort
```

**기대 결과**:

```
.claude/commands/analyze.md            ← 분석 실행 스킬
.claude/commands/validate-models.md    ← dbt 검증 스킬
.claude/commands/generate-report.md    ← 리포트 생성 스킬
.claude/hooks/bq-cost-guard.sh         ← BigQuery 비용 가드 훅
.claude/hooks/dbt-auto-test.sh         ← dbt 자동 테스트 훅
.claude/settings.json                  ← 권한·훅 설정
```

---

## 사이클 요약: 모듈 2 산출물 맵

```
┌─────────────────────────────────────────────────────────────────────┐
│                    모듈 2 학습 사이클 요약                            │
├────────────────┬────────────────────────────────────────────────────┤
│ Phase 1        │ 스킬/훅 없이 DAU 분석 요청                          │
│ (관찰)         │ → dry-run 미수행, 경로 위반, 완료 증거 부재 관찰       │
│                │                                                    │
│    입력        │ • AGENTS.md (모듈 1), dbt 마트 모델, 합성 데이터     │
│    산출물      │ • 관찰 로그 2건, 관찰 노트 (6건 문제 기록)            │
├────────────────┼────────────────────────────────────────────────────┤
│ Phase 2        │ 문제를 스킬/훅 컴포넌트로 매핑                       │
│ (수정)          │ → "스킬=올바른 경로 제공, 훅=위험한 경로 차단"       │
│                │                                                    │
│    입력        │ • Phase 1 관찰 노트, 수정 질문 4개                   │
│    산출물      │ • 수정 답변 문서, 문제-컴포넌트 매핑 표 (6행)          │
├────────────────┼────────────────────────────────────────────────────┤
│ Phase 3        │ 스킬 3개 + 훅 2개 + settings.json 구현              │
│ (창작)          │ → 동일 프롬프트 재실행으로 6건 모두 개선 확인         │
│                │                                                    │
│    입력        │ • Phase 2 매핑 표, examples/ 참조 템플릿             │
│    산출물      │ • .claude/commands/analyze.md                       │
│                │ • .claude/commands/validate-models.md               │
│                │ • .claude/commands/generate-report.md               │
│                │ • .claude/hooks/bq-cost-guard.sh                   │
│                │ • .claude/hooks/dbt-auto-test.sh                   │
│                │ • .claude/settings.json                            │
│                │ • before/after 비교 기록                             │
└────────────────┴────────────────────────────────────────────────────┘
```

---

## 시간 배분 가이드

| Phase | 활동 | 소요 시간 |
|-------|------|-----------|
| Phase 1 | 관찰 1-1: 스킬 없이 DAU 분석 | 20분 |
| Phase 1 | 관찰 1-2: 비용 위반 시나리오 | 20분 |
| Phase 2 | 수정 질문 답변 작성 | 15분 |
| Phase 2 | 문제-컴포넌트 매핑 표 작성 | 15분 |
| Phase 3 | `/analyze` 스킬 생성 + 테스트 | 15분 |
| Phase 3 | `/validate-models` 스킬 생성 | 10분 |
| Phase 3 | 훅 설정 (settings.json + 스크립트) | 15분 |
| Phase 3 | before/after 비교 검증 | 10분 |
| **합계** | | **약 2시간** |

---

## 자기 점검 체크리스트

Phase 3 완료 후, 다음 모듈로 진행하기 전에 확인합니다:

| # | 항목 | 검증 방법 | 성공 기준 |
|---|------|-----------|-----------|
| 1 | `/analyze` 스킬이 동작하는가? | Claude Code에서 `/analyze` 실행 | marimo 노트북 파일이 `notebooks/` 경로에 생성됨 |
| 2 | 훅이 settings.json에 등록되어 있는가? | `cat .claude/settings.json \| jq '.hooks'` 실행 | PreToolUse, PostToolUse 훅이 각각 1개 이상 존재 |
| 3 | 비용 가드 훅이 대용량 쿼리를 차단하는가? | 1GB 초과 쿼리를 의도적으로 실행 시도 | 차단 메시지가 출력되고 쿼리가 실행되지 않음 |
| 4 | 완료 증거 파일이 생성되는가? | `/analyze` 실행 후 `ls evidence/` | `analysis_<N>.json` 파일이 존재하고 JSON 파싱 가능 |
| 5 | before/after 비교에서 행동 개선이 확인되는가? | Phase 1과 동일 프롬프트 재실행 결과 비교 | 6건 관찰 항목 중 4건 이상 개선 |

---

## 다음 모듈과의 연결

모듈 2에서 만든 스킬과 훅은 **모듈 3(오케스트레이션)**의 기반이 됩니다:

- `/analyze` 스킬 → GitHub Actions에서 `claude "/analyze ..."` 로 호출
- `/validate-models` 스킬 → stage:5-extract 단계에서 자동 실행
- 비용 가드 훅 → CI 환경에서도 동일하게 적용되어 자동 파이프라인의 비용 안전성 보장
- 완료 증거 JSON → 각 stage 완료 코멘트에 증거로 첨부

모듈 3에서는 이 스킬/훅을 **7단계 자동 워크플로** 안에서 라벨 전환과 함께 호출하는 오케스트레이션 레이어를 구축합니다.
