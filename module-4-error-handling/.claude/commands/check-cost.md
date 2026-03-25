# /check-cost — BigQuery 쿼리 비용 사전 추정

Frozen snapshot from Module 2 output (prerequisite for Module 4).
BigQuery dry-run을 사용하여 쿼리 실행 전 비용을 추정합니다.

## Input
- `$ARGUMENTS`: SQL 쿼리 또는 자연어 설명 (예: "SELECT count(*) FROM analytics.fct_daily_active_users")

## Execution Steps
1. `$ARGUMENTS`가 SQL이면 직접 사용, 자연어면 적절한 SQL 생성
2. dry-run 실행: `bq query --dry_run --use_legacy_sql=false "$SQL"`
3. 스캔 바이트 추출 및 비용 계산 ($5/TB on-demand)
4. 안전성 판단:
   - ✅ Safe: < 500MB
   - ⚠️ Warning: 500MB ~ 1GB
   - ❌ Dangerous: > 1GB
5. evidence/query_cost_log.json에 결과 기록

## Output
```
=== BigQuery 비용 추정 ===
쿼리: [SQL]
스캔 예상: [N] MB ([N] bytes)
비용 추정: $[N] (on-demand $5/TB)
판정: [✅ Safe / ⚠️ Warning / ❌ Dangerous]
```

- `evidence/query_cost_log.json` — 비용 추정 로그

## Constraints
- 실제 쿼리를 실행하지 않음 (dry-run만 실행)
- 환경 변수 사용 (프로젝트 ID, 데이터셋명 하드코딩 금지)
- BQ_COST_LIMIT_BYTES 환경 변수 참조
