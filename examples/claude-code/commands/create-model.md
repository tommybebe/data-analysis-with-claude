# /create-model — dbt 모델 생성 스킬

프로젝트 규약에 맞는 dbt 모델 파일을 스캐폴딩합니다.
계층(staging / intermediate / mart)을 선택하면 해당 규약에 맞는 파일 구조를 자동 생성합니다.

## 입력

- `$ARGUMENTS`: 모델 생성 요청 설명
  - 예: `staging events 테이블에서 필터링된 세션 데이터`
  - 예: `mart 일별 수익 집계 fct_daily_revenue`
  - 예: `intermediate 사용자별 주간 활동 집계`

## 실행 절차

### 1단계: 요청 파싱
- 계층 파악: staging / intermediate / mart
- 모델명 결정 (네이밍 규칙 적용)
- 소스 모델 또는 테이블 확인

### 2단계: 계층별 파일 경로 결정

| 계층 | 경로 | 접두사 |
|------|------|--------|
| Staging | `models/staging/stg_<소스>.sql` | `stg_` |
| Intermediate | `models/intermediate/int_<내용>.sql` | `int_` |
| Mart (팩트) | `models/marts/fct_<프로세스>.sql` | `fct_` |
| Mart (디멘전) | `models/marts/dim_<엔티티>.sql` | `dim_` |

### 3단계: SQL 파일 생성

**Staging 템플릿**:
```sql
{{ config(materialized='view') }}

-- stg_<source_table>.sql
-- 소스 데이터를 정규화하고 컬럼명을 표준화

with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
),

renamed as (
    select
        -- 기본 식별자
        <id_column> as <entity>_id,
        -- 날짜/시간
        timestamp_micros(<timestamp_column>) as event_at,
        -- 측정값
        <metric_column>
    from source
    where <filter_condition>
)

select * from renamed
```

**Mart (팩트) 템플릿**:
```sql
{{ config(
    materialized='table',
    partition_by={
        'field': '<date_column>',
        'data_type': 'date'
    },
    cluster_by=['<cluster_column>']
) }}

-- fct_<business_process>.sql
-- <비즈니스 프로세스> 집계 팩트 테이블

with base as (
    select * from {{ ref('<upstream_model>') }}
),

aggregated as (
    select
        <group_by_columns>,
        count(distinct <id_column>) as <metric_name>,
        count(*) as event_count
    from base
    group by <group_by_columns>
)

select * from aggregated
```

### 4단계: schema.yml 업데이트
해당 계층의 `schema.yml`에 모델 정의 및 테스트 추가:
```yaml
models:
  - name: <model_name>
    description: "<모델 설명>"
    columns:
      - name: <pk_column>
        description: "기본키"
        data_tests:
          - unique
          - not_null
      - name: <date_column>
        description: "집계 날짜"
        data_tests:
          - not_null
```

### 5단계: 빌드 검증
```bash
# 모델 컴파일 (SQL 생성 확인, 비용 없음)
dbt compile --select <model_name>

# 빌드 및 테스트
dbt run --select <model_name>
dbt test --select <model_name>
```

## 출력 형식

```
## 모델 생성 완료

### 생성된 파일
- 📄 models/marts/fct_<name>.sql
- 📋 models/marts/schema.yml (업데이트됨)

### 검증 결과
- ✅ dbt compile: 성공
- ✅ dbt run: 성공
- ✅ dbt test: N개 통과

### 다음 단계
- notebooks/에서 새 모델을 사용하는 분석 노트북 작성
- /check-cost 로 쿼리 비용 사전 확인 권장
```

## 완료 증거

- [ ] SQL 파일이 올바른 경로에 생성됨
- [ ] `schema.yml`에 primary key 테스트가 정의됨
- [ ] `dbt compile`이 성공적으로 실행됨
- [ ] `dbt run`과 `dbt test`가 통과됨
