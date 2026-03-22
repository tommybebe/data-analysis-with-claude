# /validate-models — dbt 모델 검증 스킬

dbt 모델을 빌드하고 테스트를 실행하여 결과를 요약합니다.

## 입력

- `$ARGUMENTS` (선택): 특정 모델명. 미지정 시 전체 모델 실행.

## 실행 절차

1. **dbt deps**: 패키지 의존성 설치 확인
2. **dbt run**: 모델 빌드 실행
   - 특정 모델 지정 시: `dbt run --select $ARGUMENTS`
   - 전체 실행 시: `dbt run`
3. **dbt test**: 데이터 테스트 실행
   - 특정 모델 지정 시: `dbt test --select $ARGUMENTS`
   - 전체 실행 시: `dbt test`
4. **결과 요약**: 통과/실패 테스트 수, 실패 원인 분석

## 비용 보호

- 실행 전 `dbt ls --select $ARGUMENTS` 로 실행 대상 모델 목록 확인
- mart 모델이 `materialized='table'`인 경우 BigQuery 비용 발생 주의
- `--defer` 플래그 사용 가능 여부 확인

## 출력 형식

```
## dbt 검증 결과

### 빌드 (dbt run)
- ✅ 성공: N개 모델
- ❌ 실패: N개 모델
  - model_name: 에러 메시지

### 테스트 (dbt test)
- ✅ 통과: N개
- ❌ 실패: N개
- ⚠️ 경고: N개

### 실패 테스트 상세
| 테스트명 | 모델 | 실패 원인 |
|---------|------|----------|
| ...     | ...  | ...      |
```

## 완료 증거

- [ ] `dbt run` 실행 결과가 `target/run_results.json`에 저장됨
- [ ] `dbt test` 실행 결과가 `target/run_results.json`에 저장됨
- [ ] 실패한 테스트가 0건이거나, 실패 원인이 문서화됨
