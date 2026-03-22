# /explore-data — 데이터 탐색 스킬

BigQuery 테이블 또는 dbt 모델의 스키마, 데이터 품질, 기초 통계를 빠르게 파악합니다.
새 데이터셋 탐색이나 분석 시작 전 데이터 이해를 위해 사용합니다.

## 입력

- `$ARGUMENTS`: 탐색할 대상
  - BigQuery 테이블: `project.dataset.table_name`
  - dbt 모델명: `fct_daily_active_users`
  - dbt 소스: `fittrack_raw.events`

## 실행 절차

### 1단계: 스키마 확인
```bash
# BigQuery 테이블 스키마 조회 (비용 없음)
bq show --format=prettyjson <table_reference>
```

또는 dbt 모델의 경우 `models/` 디렉토리에서 `schema.yml` 참조.

### 2단계: 행 수 및 기간 파악 (dry-run 먼저)
```sql
-- dry-run으로 비용 확인 후 실행
SELECT
  COUNT(*) AS total_rows,
  MIN(<date_column>) AS min_date,
  MAX(<date_column>) AS max_date
FROM `<table_reference>`
```

### 3단계: 컬럼별 기초 통계
주요 수치형 컬럼에 대해:
```sql
SELECT
  COUNT(*) AS total,
  COUNT(DISTINCT <column>) AS unique_values,
  MIN(<column>) AS min_val,
  MAX(<column>) AS max_val,
  AVG(<column>) AS avg_val
FROM `<table_reference>`
LIMIT 0  -- dry-run 시 사용
```

### 4단계: 데이터 품질 체크
- NULL 값 비율 확인
- 중복 레코드 확인 (primary key 컬럼)
- 날짜 범위의 공백(gap) 확인

### 5단계: 탐색 결과 요약

## 비용 주의

- 모든 쿼리는 dry-run으로 비용 확인 후 실행
- `COUNT(*)`, `MIN()`, `MAX()`도 파티션 필터 없이 전체 스캔 발생
- 가능하면 `TABLESAMPLE SYSTEM (1 PERCENT)` 활용하여 비용 절감:
  ```sql
  SELECT * FROM `<table>` TABLESAMPLE SYSTEM (1 PERCENT)
  ```

## 출력 형식

```
## 데이터 탐색 결과: <테이블명>

### 스키마
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| user_id | STRING | 사용자 고유 ID |
| event_date | DATE | 이벤트 발생 일자 |
| ...     | ...  | ... |

### 기본 통계
- 총 행 수: X,XXX,XXX
- 기간: YYYY-MM-DD ~ YYYY-MM-DD
- 파티션 컬럼: event_date

### 데이터 품질
| 항목 | 결과 |
|------|------|
| user_id NULL 비율 | 0.0% |
| 중복 레코드 | 없음 |
| 날짜 공백 | 없음 |

### 쿼리 비용
- 탐색 시 총 스캔량: X.X GB
- 예상 비용: $X.XX USD

### 주요 발견
- [탐색 중 발견한 특이사항]
```

## 완료 증거

- [ ] 테이블 스키마와 컬럼 설명이 확인됨
- [ ] 데이터 행 수와 기간 범위가 파악됨
- [ ] NULL 비율과 중복 여부가 체크됨
- [ ] 모든 쿼리가 dry-run을 먼저 실행함
