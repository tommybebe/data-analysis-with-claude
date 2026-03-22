# /analyze — 분석 실행 스킬

GitHub Issue의 분석 요청을 파싱하여 dbt 쿼리와 marimo 노트북을 생성합니다.

## 입력

- `$ARGUMENTS`: GitHub Issue 번호 또는 분석 요청 텍스트

## 실행 절차

1. **분석 요청 파싱**: 이슈에서 분석 대상 지표, 기간, 세그먼트를 추출
2. **기존 모델 확인**: `models/` 디렉토리에서 사용 가능한 dbt 모델 탐색
3. **필요 시 추가 쿼리 작성**: 기존 mart 모델로 충분하지 않으면 임시 쿼리 생성
4. **marimo 노트북 생성**: 분석 결과를 시각화하는 marimo 노트북 작성

## dbt 모델 참조 규칙

- `{{ ref('fct_daily_active_users') }}` — DAU 일별 집계
- `{{ ref('fct_monthly_active_users') }}` — MAU 월별 집계
- `{{ ref('fct_retention_cohort') }}` — 코호트 리텐션
- 새 모델 생성 시 반드시 `models/marts/` 하위에 `fct_` 또는 `dim_` 접두사 사용

## marimo 노트북 규약

- 파일 경로: `notebooks/analysis_<issue_number>.py`
- 첫 번째 셀: 분석 요약 (제목, 기간, 핵심 발견)
- 마지막 셀: 결론 및 제안
- 차트 제목과 축 레이블은 한국어로 작성
- BigQuery 연결은 `google.cloud.bigquery.Client()` 사용

## 출력

- 생성된 파일 목록과 경로
- 각 파일의 목적 간략 설명

## 완료 증거

- [ ] marimo 노트북 파일이 `notebooks/` 디렉토리에 생성됨
- [ ] `dbt run` 실행 시 관련 모델이 정상 빌드됨
- [ ] 노트북 내 쿼리가 dry-run 통과 (비용 한도 이내)
