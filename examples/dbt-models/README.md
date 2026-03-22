# dbt 프로젝트: mobile_analytics

B2C 모바일 앱의 DAU/MAU 분석을 위한 dbt 모델 컬렉션.
합성 이벤트 데이터를 BigQuery on-demand 환경에서 변환합니다.

## 프로젝트 구조

```
dbt-models/
├── dbt_project.yml          # 프로젝트 설정 (레이어별 구체화 전략)
├── packages.yml             # dbt 패키지 의존성 (dbt-utils, dbt-expectations)
├── profiles.yml.example     # BigQuery 연결 설정 예시
│
├── macros/
│   └── analysis_helpers.sql # 공통 매크로 (KST 변환, 비율 계산, 세그먼트 분류)
│
├── seeds/                   # 참조 데이터 CSV (dbt seed로 BigQuery에 적재)
│   ├── seeds.yml            # 시드 컬럼 정의 및 테스트
│   └── event_type_metadata.csv  # 이벤트 유형 메타데이터 (한/영 표시명, 카테고리)
│
├── snapshots/               # SCD Type 2 이력 추적 (dbt snapshot)
│   └── snap_user_subscription.sql  # 사용자 구독 등급 변경 이력
│
├── analyses/                # 탐색적 SQL (구체화 없음, dbt compile 후 실행)
│   ├── 01_dau_trend_exploration.sql  # DAU 이동 평균·전주 대비 변화율
│   └── 02_funnel_analysis.sql        # 온보딩·운동·결제 퍼널 분석
│
├── tests/
│   ├── assert_dau_lte_mau.sql            # DAU ≤ MAU 무결성 검사
│   ├── assert_retention_rate_bounded.sql  # 리텐션 비율 범위 검사 (0~1)
│   └── assert_streak_positive.sql         # 연속 활동 일수(streak) 양수 검사
│
├── models/
│   ├── staging/             # 레이어 1: 원시 데이터 클렌징 (VIEW)
│   │   ├── sources.yml      # 소스 테이블 정의 및 신선도 검사
│   │   ├── schema.yml       # 스테이징 모델 컬럼 정의 및 테스트
│   │   ├── stg_events.sql   # 이벤트 로그 (KST 변환, JSON 파싱)
│   │   ├── stg_users.sql    # 사용자 프로필 (가입일 KST, 경과일)
│   │   └── stg_sessions.sql # 세션 데이터 (비정상 종료 처리)
│   │
│   ├── intermediate/        # 레이어 2: 비즈니스 로직 중간 집계 (VIEW)
│   │   ├── schema.yml       # 중간 모델 컬럼 정의 및 테스트
│   │   ├── int_user_daily_activity.sql    # 사용자-일자별 활동 집계
│   │   ├── int_user_metrics.sql           # 사용자별 누적 지표 + 세그멘테이션
│   │   └── int_user_rolling_metrics.sql   # 7일 이동 평균 + 연속 활동 streak
│   │
│   └── marts/               # 레이어 3: 최종 분석 테이블 (TABLE + 파티션)
│       ├── schema.yml       # 마트 모델 컬럼 정의 및 테스트
│       ├── fct_daily_active_users.sql   # DAU 집계 (날짜·플랫폼별)
│       ├── fct_monthly_active_users.sql # MAU 집계 (DAU/MAU stickiness)
│       ├── fct_retention_cohort.sql     # 코호트 리텐션 (week-N 잔존율)
│       ├── fct_feature_engagement.sql   # 기능별 참여도 (채택률·완료율)
│       ├── fct_revenue_analysis.sql     # 수익 분석 (ARPU·ARPPU·전환율)
│       └── fct_user_segments.sql        # 사용자 세그먼트 스냅샷
```

## 레이어 설계 원칙

### Staging (스테이징)
- **구체화**: `VIEW` — 실제 데이터 스캔은 mart 구체화 시 1회만 발생
- **역할**: 원시 데이터 클렌징, 타임존 변환 (UTC → KST), 타입 캐스팅
- **규칙**: `source()` 참조만 허용, 집계 없음, 1:1 행 변환

### Intermediate (중간)
- **구체화**: `VIEW` — staging과 동일한 비용 절감 전략
- **역할**: 여러 staging 모델 결합, 비즈니스 로직 캡슐화
- **규칙**: `ref()` 참조만 허용, mart에서 중복 로직 제거를 위해 존재

### Marts (마트)
- **구체화**: `TABLE` + 파티션 — 반복 쿼리 비용 최소화
- **역할**: 최종 분석 지표 제공, marimo 노트북 데이터 소스
- **규칙**: 분석가·대시보드가 직접 쿼리하는 레이어

## 데이터 흐름

```
BigQuery raw.*          (원시 테이블, sources.yml에 정의)
    ↓
staging.*               (클렌징 VIEW: stg_events, stg_users, stg_sessions)
    ↓
intermediate.*          (중간 집계 VIEW: int_user_daily_activity, int_user_metrics)
    ↓
marts.*                 (최종 TABLE: fct_daily_active_users, fct_monthly_active_users,
                                     fct_retention_cohort, fct_feature_engagement,
                                     fct_revenue_analysis, fct_user_segments)
```

## 빠른 시작

### 1. 환경 설정

```bash
# dbt 패키지 설치
dbt deps

# BigQuery 연결 확인
dbt debug
```

### 2. 데이터 적재

```bash
# 합성 데이터 생성 후 BigQuery에 적재
python generate_synthetic_data.py

# 참조 데이터(seeds) BigQuery에 적재
dbt seed

# 소스 데이터 신선도 확인
dbt source freshness
```

### 3. 모델 실행

```bash
# 전체 실행
dbt run

# 레이어별 실행
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# 특정 모델만 실행
dbt run --select fct_daily_active_users

# 스냅샷 실행 (구독 등급 변경 이력 추적)
dbt snapshot
```

### 4. 테스트 실행

```bash
# 전체 테스트
dbt test

# 모델별 테스트
dbt test --select stg_events

# 소스 테스트 (신선도 + 데이터 품질)
dbt test --select source:mobile_app_raw

# 커스텀 테스트만 실행
dbt test --select assert_dau_lte_mau assert_retention_rate_bounded assert_streak_positive
```

### 5. 탐색적 분석 실행

```bash
# analyses/ 파일 SQL로 컴파일 (BigQuery에서 직접 실행 가능)
dbt compile --select 01_dau_trend_exploration
dbt compile --select 02_funnel_analysis

# 컴파일된 SQL 위치
# target/compiled/mobile_analytics/analyses/
```

## 매크로 활용

`macros/analysis_helpers.sql`에 반복 패턴을 추상화한 공통 매크로가 정의되어 있습니다.

| 매크로 | 설명 | 사용 예 |
|--------|------|---------|
| `utc_to_kst(col)` | UTC → KST 타임스탬프 변환 | `{{ utc_to_kst('event_timestamp') }}` |
| `utc_to_kst_date(col)` | UTC → KST 기준 DATE 추출 | `{{ utc_to_kst_date('event_timestamp') }}` |
| `safe_rate(num, denom)` | NULL-safe 비율 계산 | `{{ safe_rate('completes', 'starts') }}` |
| `event_count(type)` | 이벤트 유형별 COUNTIF | `{{ event_count('workout_start') }}` |
| `revenue_sum()` | 구매 이벤트 수익 합산 | `{{ revenue_sum() }}` |
| `activity_segment_label(days, last)` | 활동 세그먼트 CASE WHEN | `{{ activity_segment_label('active_days', 'days_since') }}` |
| `revenue_segment_label(revenue)` | 수익 세그먼트 CASE WHEN | `{{ revenue_segment_label('lifetime_revenue_krw') }}` |

## 커스텀 데이터 테스트

`tests/` 디렉토리에 비즈니스 규칙을 검증하는 커스텀 SQL 테스트가 있습니다.

| 테스트 | 검증 내용 |
|--------|-----------|
| `assert_dau_lte_mau` | DAU는 항상 해당 월의 MAU 이하여야 함 |
| `assert_retention_rate_bounded` | 잔존율은 0~1 범위, week-0은 정확히 1.0 |
| `assert_streak_positive` | 연속 활동 일수는 항상 1 이상, 라벨 값 유효성 검사 |

```bash
# 커스텀 테스트만 실행
dbt test --select assert_dau_lte_mau
dbt test --select assert_retention_rate_bounded
dbt test --select assert_streak_positive
```

## 시드(Seeds) 활용

`seeds/` 디렉토리에 참조 데이터 CSV 파일이 있습니다.

| 시드 | 내용 | 활용 |
|------|------|------|
| `event_type_metadata` | 이벤트 유형별 한/영 표시명, 카테고리, 전환 이벤트 여부 | 리포트 레이블, stg_events 조인 |

```bash
# 시드 적재 (BigQuery에 테이블로 생성)
dbt seed

# 모델에서 참조
-- SELECT e.*, m.display_name_ko FROM stg_events e
-- LEFT JOIN {{ ref('event_type_metadata') }} m ON e.event_type = m.event_type
```

## 스냅샷(Snapshots) 활용

`snapshots/` 디렉토리에 SCD Type 2 이력 추적 모델이 있습니다.

| 스냅샷 | 추적 대상 | 활용 |
|--------|-----------|------|
| `snap_user_subscription` | 사용자 구독 등급(subscription_tier) 변경 이력 | 업그레이드 분석, 이탈 후 복귀 패턴 |

```bash
# 스냅샷 실행 (변경분만 처리)
dbt snapshot

# 현재 구독 등급 조회 (스냅샷에서)
-- SELECT * FROM snap_user_subscription WHERE dbt_valid_to IS NULL
```

## 탐색적 분석(Analyses) 활용

`analyses/` 디렉토리에 탐색적 SQL 파일이 있습니다. 구체화되지 않으므로 `dbt compile` 후 BigQuery에서 직접 실행합니다.

| 분석 | 주요 패턴 | 활용 |
|------|-----------|------|
| `01_dau_trend_exploration` | 7일/30일 이동 평균, 전주 대비 변화율, 플랫폼 비율 | DAU 추세선 파악, 노이즈 제거 |
| `02_funnel_analysis` | 온보딩 퍼널, 운동 퍼널, 채널별 전환율 비교 | 단계별 이탈률, 마케팅 채널 품질 평가 |

## BigQuery 비용 관리

| 전략 | 설명 |
|------|------|
| **VIEW 레이어** | staging/intermediate는 VIEW로 실제 스캔 최소화 |
| **파티셔닝** | mart 테이블은 날짜 파티션 적용, 쿼리 범위 제한 |
| **최대 바이트 제한** | `profiles.yml`에서 `maximum_bytes_billed: 1GB` 설정 |
| **합성 데이터 규모** | 약 500K 이벤트, ~150K 세션, ~10K 사용자 (약 10MB 수준) |

> **참고**: 합성 데이터 기준 전체 `dbt run` 실행 비용 < $0.01 (BigQuery on-demand)

## 주요 모델 설명

### `int_user_rolling_metrics` ← 중간 레이어
사용자별 7일 이동 평균, 전주 대비 참여도 변화율, 연속 활동 일수(streak) 계산.
이탈 위험 조기 경고(`engagement_trend='at_risk'`), 재참여 타이밍, streak 기반 게임화 알림에 활용.

**주요 컬럼**: `user_id`, `activity_date`, `engagement_7d_avg`, `engagement_wow`, `engagement_trend`, `current_streak_days`, `streak_label`

**⚠️ 비용 주의**: 파티션 필터 없이 전체 조회 시 스캔량이 큼. `WHERE activity_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)` 등 범위 제한 필요.

### `snap_user_subscription` ← 스냅샷
사용자 구독 등급(`subscription_tier`) 변경 이력을 SCD Type 2 방식으로 추적.
업그레이드/다운그레이드 분석, 이탈 후 복귀 패턴, 특정 기간 기준 구독 등급 조회에 활용.

**주요 컬럼**: `user_id`, `subscription_tier`, `is_active`, `dbt_valid_from`, `dbt_valid_to`

### `fct_daily_active_users`
DAU 분석의 핵심 테이블. 날짜·플랫폼별로 집계되며, marimo DAU/MAU 노트북의 주요 데이터 소스.

**주요 컬럼**: `activity_date`, `platform`, `dau`, `new_users`, `stickiness`, `total_revenue`

### `fct_monthly_active_users`
MAU 및 DAU/MAU stickiness 계산. `fct_daily_active_users`를 월 단위로 롤업.

**주요 컬럼**: `activity_month`, `mau`, `stickiness`, `avg_active_days_per_user`

### `fct_retention_cohort`
가입 주차별 코호트 리텐션. week-0부터 week-12까지 잔존율을 행 단위로 제공.
marimo 노트북에서 피벗 후 히트맵으로 시각화.

**주요 컬럼**: `cohort_week`, `weeks_since_signup`, `retention_rate`

### `fct_feature_engagement`
운동·목표·소셜·구매 기능의 일별 채택률과 완료율 집계.
기능별 A/B 테스트 결과 평가 및 제품 개선 우선순위 결정에 활용.

**주요 컬럼**: `activity_date`, `dau`, `workout_adoption_rate`, `workout_completion_rate`, `goal_adoption_rate`, `social_adoption_rate`, `purchase_conversion_rate`

**분석 예시**: "워크아웃 완료율이 낮아지는 요일 패턴이 있는가? 목표 달성률이 운동 완료율과 상관관계가 있는가?"

### `fct_revenue_analysis`
구독 등급별 월간 ARPU/ARPPU, 결제 전환율, 수익 기여 비율 집계.
LTV 추정, 마케팅 ROI 분석, 구독 티어 업셀링 전략 수립에 활용.

**주요 컬럼**: `activity_month`, `subscription_tier`, `mau`, `arpu_krw`, `arppu_krw`, `payment_conversion_rate`, `revenue_share_of_month`

**분석 예시**: "premium 등급 사용자의 ARPU가 free 등급 대비 얼마나 높은가? 어느 유입 채널이 결제 전환율이 높은가?"

### `fct_user_segments`
activity_segment × revenue_segment 교차 기준 사용자 분포 스냅샷.
각 세그먼트별 행동 지표(활동 밀도, 운동 완료율)와 수익 지표(LTV, 결제 비율), 재참여 우선순위 점수 포함.

**주요 컬럼**: `activity_segment`, `revenue_segment`, `user_count`, `user_share`, `avg_ltv_krw`, `activation_rate`, `reengagement_priority_score`

**분석 예시**: "churned × high_value 사용자(이탈한 고가치 사용자)가 몇 명이며, 어느 채널 출신이 많은가?"
