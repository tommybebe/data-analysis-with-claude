# /check-cost — BigQuery 쿼리 비용 확인

SQL 쿼리 또는 파일을 dry-run으로 실행하여 예상 스캔 바이트와 비용을 확인합니다.

## 입력

- `$ARGUMENTS`: SQL 쿼리 문자열 또는 `.sql` 파일 경로

## 실행 절차

1. **입력 유형 판별**
   - 파일 경로면 파일 내용 읽기 (`Read` 도구 사용)
   - 직접 SQL 문자열이면 그대로 사용

2. **dry-run 실행**
   ```bash
   bq query --dry_run --use_legacy_sql=false --format=json "<SQL>"
   ```

3. **비용 계산 및 분류**
   - 스캔 바이트 → MB/GB 단위 변환
   - BigQuery on-demand 가격 기준: $5/TB
   - 예상 비용(USD) 계산

4. **결과 출력**: 아래 형식으로 요약 보고

## 출력 형식

```
## BigQuery 비용 확인 결과

📊 예상 스캔량: X.X GB (X,XXX,XXX,XXX bytes)
💰 예상 비용:  $X.XX USD (on-demand, $5/TB 기준)

상태: ✅ 안전 / ⚠️ 주의 / ❌ 위험

[안전 기준]
- ✅ 1GB 이하: 실행 가능
- ⚠️ 1~10GB: 실행 전 확인 권장
- ❌ 10GB 초과: 쿼리 최적화 필요
```

## 최적화 제안 (비용 초과 시)

비용이 임계값을 초과하면 다음 최적화 방법을 제안합니다:

- `WHERE` 절에 날짜 파티션 필터 추가
- `SELECT *` → 필요한 컬럼만 명시
- 대용량 테이블 조인 전 서브쿼리로 필터링
- mart 모델(`fct_*`) 사용으로 집계 전 데이터 활용

## 완료 증거

- [ ] dry-run 결과에서 `totalBytesProcessed` 값 확인됨
- [ ] 스캔량이 MB/GB 단위로 사람이 읽기 쉽게 변환됨
- [ ] 비용 임계값 초과 시 최적화 방안이 제안됨
