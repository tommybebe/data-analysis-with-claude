# /validate — 모듈 2 완료 검증

모듈 2의 슬래시 커맨드 설정 상태를 검증합니다. **자동 검증 스크립트를 실행**하고 결과를 한국어로 보고하세요.

> **📖 학습 참고**: 이 `/validate` 커맨드 파일 자체가 슬래시 커맨드의 실제 예시입니다.
> 아래의 Input → Execution Steps → Output → Constraints 구조를 학습자가 작성할
> `/analyze`, `/check-cost`, `/validate-models`, `/generate-report`에도 동일하게 적용하세요.
> 이 파일을 참고 템플릿으로 활용할 수 있습니다.

---

## Input

- `$ARGUMENTS`: 사용하지 않음 (무시됨)
- 이 커맨드는 인자 없이 `/validate`만으로 실행합니다

> **💡 학습 포인트**: `/validate`는 인자가 없는 단순 커맨드입니다. `/analyze`처럼 `$ARGUMENTS`를
> 파싱해야 하는 커맨드와 비교하면, 커맨드 설계 시 입력 유무에 따른 구조 차이를 이해할 수 있습니다.

## Execution Steps

### 1단계: 자동 검증 스크립트 실행

```bash
bash scripts/validate.sh
```

스크립트가 다음 7개 항목을 **실제 기능 테스트**로 검증합니다 (파일 존재 확인이 아닌 내용 검증):

| # | 항목 | 기능 검증 내용 |
|---|------|---------------|
| 0 | 슬래시 커맨드 파일 | 4개 파일 존재 + 최소 200바이트 + Input/Steps/Output 섹션 포함 확인 |
| 1 | /analyze 커맨드 구조 | `$ARGUMENTS` 변수, marimo 노트북 생성, dbt 모델 활용, 비용 사전 확인 — 4개 중 3개 이상 포함 |
| 2 | /check-cost 커맨드 구조 | `--dry_run` 사용, 바이트/MB/GB 출력, 안전 판단 기준(Safe/Warning/Dangerous), `query_cost_log` 저장 |
| 3 | /validate-models 구조 | `dbt test` 실행, `dbt_test_results.json` 저장, total_tests/passed/failed 필드 |
| 4 | /generate-report 구조 | `marimo export` 사용, `report_manifest.json` 저장, outputs[].format/path 필드 |
| 5 | 회고 기록 | evidence/module-2-retrospective.md 존재 및 50바이트 이상 내용 작성 확인 |
| 6 | 환경 변수 | `.env` 파일 존재 + `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 값 설정 + 인증 파일 경로 접근 가능 여부 |

> **💡 학습 포인트**: 이 단계처럼 각 Execution Step은 에이전트가 **순서대로** 실행할 구체적 동작입니다.
> 학습자가 작성하는 커맨드에서도 "1. 무엇을 하고 → 2. 결과를 어떻게 처리하고 → 3. 어디에 저장"의
> 순차 워크플로를 명확하게 정의하세요.

### 2단계: 결과 해석 및 보고

스크립트 출력을 그대로 사용자에게 보여주세요. 추가로:

- ❌ 항목이 있으면: 각 실패 항목별 **구체적인 해결 방법**을 안내
  - 커맨드 파일 누락: `.claude/commands/` 디렉터리에 analyze.md, check-cost.md, validate-models.md, generate-report.md 생성 필요
  - /analyze: `$ARGUMENTS` 참조, marimo 노트북 생성 지시, dbt 모델 참조 추가 안내
  - /check-cost: `bq --dry_run` 기반 비용 추정 → 안전 수준 판단 → 로그 저장 구조 안내
  - /validate-models: `dbt test` 실행 → JSON 결과 저장 → 통계 필드 구조 안내
  - /generate-report: `marimo export` → 매니페스트 JSON 저장 → outputs 배열 구조 안내
  - 회고: 커맨드-훅 역할 분담 분석 작성 안내
  - 환경 변수: `.env.example`을 `.env`로 복사하고 `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 값 입력 안내
- ⚠️ 항목만 있으면: 경고 내용과 선택적 해결 방법 안내
- 모든 항목 ✅이면: "🎉 모듈 2 완료! 모듈 3(권한 오케스트레이션)으로 진행하세요."

### 3단계: 스크립트 실행 불가 시 수동 검증

스크립트를 실행할 수 없는 경우, 아래 명령어를 **직접 실행**하여 각 항목을 검증하세요:

```bash
# 0. 슬래시 커맨드 파일 — 존재 + 최소 분량 + 필수 섹션
for cmd in analyze check-cost validate-models generate-report; do
  f=".claude/commands/${cmd}.md"
  test -f "$f" || echo "❌ ${f} 없음"
  [ $(wc -c < "$f") -ge 200 ] || echo "⚠️ ${f} 내용 부족 (200바이트 미만)"
  grep -qiE "(input|입력|argument)" "$f" || echo "⚠️ ${f}: Input 섹션 누락"
  grep -qiE "(step|단계|절차)" "$f" || echo "⚠️ ${f}: Steps 섹션 누락"
  grep -qiE "(output|출력|결과)" "$f" || echo "⚠️ ${f}: Output 섹션 누락"
done

# 1. /analyze — 핵심 요소 4개 중 3개 이상
f=".claude/commands/analyze.md"
checks=0
grep -q '\$ARGUMENTS' "$f" && checks=$((checks + 1))
grep -qiE "marimo|notebook|analyses/" "$f" && checks=$((checks + 1))
grep -qiE "fct_daily_active_users|fct_monthly_active_users|dbt" "$f" && checks=$((checks + 1))
grep -qiE "cost|비용|dry.run" "$f" && checks=$((checks + 1))
echo "analyze: ${checks}/4 요소 포함 (3 이상이면 통과)"

# 2. /check-cost — 핵심 요소 4개 중 3개 이상
f=".claude/commands/check-cost.md"
checks=0
grep -qiE "dry.run|dry_run" "$f" && checks=$((checks + 1))
grep -qiE "byte|MB|GB" "$f" && checks=$((checks + 1))
grep -qiE "safe|warning|dangerous|안전|경고|위험" "$f" && checks=$((checks + 1))
grep -qiE "query_cost_log|cost_log" "$f" && checks=$((checks + 1))
echo "check-cost: ${checks}/4 요소 포함 (3 이상이면 통과)"

# 3. /validate-models — 핵심 요소 3개 중 2개 이상
f=".claude/commands/validate-models.md"
checks=0
grep -qiE "dbt test" "$f" && checks=$((checks + 1))
grep -qiE "dbt_test_results" "$f" && checks=$((checks + 1))
grep -qiE "total_tests|passed|failed" "$f" && checks=$((checks + 1))
echo "validate-models: ${checks}/3 요소 포함 (2 이상이면 통과)"

# 4. /generate-report — 핵심 요소 3개 중 2개 이상
f=".claude/commands/generate-report.md"
checks=0
grep -qiE "marimo|export|HTML" "$f" && checks=$((checks + 1))
grep -qiE "report_manifest" "$f" && checks=$((checks + 1))
grep -qiE "format|path|outputs" "$f" && checks=$((checks + 1))
echo "generate-report: ${checks}/3 요소 포함 (2 이상이면 통과)"

# 5. 회고 기록
test -f evidence/module-2-retrospective.md && \
[ $(wc -c < evidence/module-2-retrospective.md) -gt 50 ] && \
echo "✅ 회고 작성 완료" || echo "❌ 회고 없거나 내용 부족"
```

결과를 아래 형식으로 정리하세요:

```
## 모듈 2 검증 결과

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | 슬래시 커맨드 파일 | ✅/❌ | ... |
| ... | ... | ... | ... |

총 N/7 항목 통과
```

## Output

검증 결과를 위 표 형식으로 한국어 보고합니다. 6개 항목에 대한 ✅/⚠️/❌ 판정과 상세 내역을 포함합니다.

> **💡 학습 포인트**: Output 섹션은 커맨드 실행 후 **기대되는 결과물의 형식**을 정의합니다.
> `/validate`는 텍스트 표를 출력하지만, `/check-cost`나 `/validate-models`처럼
> `evidence/` 디렉터리에 JSON 파일을 저장하는 패턴이 더 일반적입니다.
> JSON 증거 파일은 **기계 검증 가능한 산출물**로, 다음 커맨드에서 입력으로 활용할 수 있습니다.

## Constraints

- 스크립트 출력을 임의로 수정하지 않고 그대로 보고
- 실패 항목에 대해 파일 자동 생성이나 자동 수정 금지 — 학습자에게 해결 방법만 안내
- 검증 중 BigQuery 쿼리를 실행하지 않음 (오프라인 검증)
- evidence/ 파일의 내용을 직접 수정하지 않음

> **💡 학습 포인트**: Constraints는 에이전트가 **하지 말아야 할 행동**을 정의합니다.
> 훅(Hook)이 런타임에서 위반을 차단하는 반면, Constraints는 설계 시점에서 에이전트의
> 행동 범위를 제한합니다. 두 메커니즘이 보완적으로 작동하여 에이전트 안전성을 확보합니다.

---

## 📖 이 파일을 커맨드 설계 참고 자료로 활용하기

이 `/validate` 커맨드 파일은 다음 슬래시 커맨드 설계 패턴을 보여줍니다:

| 패턴 | 이 파일의 예시 | 학습자 커맨드에 적용 |
|------|--------------|---------------------|
| **섹션 구조** | Input → Execution Steps → Output → Constraints | 4개 커맨드 모두 동일 구조 사용 |
| **구체적 단계** | "1단계: 스크립트 실행 → 2단계: 결과 해석 → 3단계: 대안 경로" | 각 커맨드의 워크플로를 순차 단계로 분해 |
| **조건부 분기** | ❌/⚠️/✅에 따른 다른 응답 지시 | `/check-cost`의 Safe/Warning/Dangerous 판단 |
| **외부 도구 활용** | `bash scripts/validate.sh` 실행 | `bq query --dry_run`, `dbt test`, `marimo export` |
| **행동 제한** | "자동 수정 금지", "쿼리 실행 금지" | 각 커맨드의 비용/보안 관련 제약 |

학습자가 작성할 4개 커맨드 파일(`.claude/commands/`에 생성)도 이와 동일한 구조를 따릅니다.
차이점은 `/validate`가 인자 없이 동작하는 반면, `/analyze`는 `$ARGUMENTS`로 동적 입력을
받아 다른 출력 파일을 생성한다는 점입니다.

#### 6. 환경 변수 수동 확인

```bash
# .env 파일 존재 + 필수 변수 값 확인
test -f .env && grep -q "GCP_PROJECT_ID=" .env && grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env
```
