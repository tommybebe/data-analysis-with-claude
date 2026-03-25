# /analyze — 분석 요청 파싱부터 marimo 노트북 생성까지

Frozen snapshot from Module 2 output (prerequisite for Module 3).
분석 요청을 파싱하여 dbt 모델을 탐색하고, 비용을 확인한 후, marimo 노트북을 생성합니다.

## Input
- `$ARGUMENTS`: 분석 요청 텍스트 (예: "2026년 1월 DAU", "1분기 플랫폼별 MAU 추이")

## Execution Steps
1. `$ARGUMENTS`에서 분석 대상 기간, 지표, 세분화 기준을 파싱
2. 사용 가능한 dbt 모델 탐색: `dbt ls --resource-type model`
3. 분석에 필요한 mart 모델 식별 (fct_daily_active_users, fct_monthly_active_users, fct_retention_cohort)
4. BigQuery dry-run으로 비용 사전 확인: `bq query --dry_run --use_legacy_sql=false "SELECT ..."`
5. 비용이 BQ_COST_LIMIT_BYTES 이내인 경우에만 진행
6. marimo 노트북 생성: `analyses/analysis_[metric]_[YYYYMM].py`
7. 노트북에 BigQuery 쿼리, 시각화, 인사이트 요약 포함
8. evidence/analysis_manifest.json에 분석 메타데이터 기록

## Output
- `analyses/analysis_[metric]_[YYYYMM].py` — marimo 노트북 파일
- `evidence/analysis_manifest.json` — 분석 실행 메타데이터

## Constraints
- 반드시 dbt mart 모델을 통해 데이터 접근 (raw 테이블 직접 접근 금지)
- BigQuery dry-run 비용 확인 후 진행
- 노트북 파일명은 analysis_[metric]_[YYYYMM].py 형식 준수
- 환경 변수 사용 (GCP_PROJECT_ID, BQ_DATASET_ANALYTICS 등 하드코딩 금지)
