# /validate-models — dbt 모델 검증 및 테스트 결과 기록

Frozen snapshot from Module 2 output (prerequisite for Module 3).
dbt 테스트를 실행하여 모델 품질을 검증하고 결과를 JSON으로 저장합니다.

## Input
- `$ARGUMENTS`: 검증 대상 모델 (선택사항, 예: "staging", "marts", 또는 특정 모델명)

## Execution Steps
1. `$ARGUMENTS`로 대상 범위 결정 (없으면 전체 모델)
2. dbt 테스트 실행: `dbt test` 또는 `dbt test --select $ARGUMENTS`
3. 테스트 결과 파싱 (통과/실패/경고/에러 수)
4. evidence/dbt_test_results.json에 결과 기록

## Output
- `evidence/dbt_test_results.json` — 테스트 결과 JSON

```json
{
  "timestamp": "2026-01-15T10:30:00+09:00",
  "total_tests": 15,
  "passed": 14,
  "failed": 1,
  "warnings": 0,
  "errors": 0,
  "failed_tests": ["test_name_here"],
  "target_selection": "$ARGUMENTS or 'all'"
}
```

## Constraints
- dbt test 실행 전 dbt compile로 문법 검증
- JSON에 total_tests, passed, failed 필드 필수 포함
- 실패한 테스트의 구체적 이름 기록
