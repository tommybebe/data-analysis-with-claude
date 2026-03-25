# 합성 데이터 생성 가이드

> **하니스 엔지니어링 for 데이터 분석** 코스 — 참고 자료
>
> 이 가이드는 코스 실습에 사용되는 합성 데이터(B2C 모바일 피트니스 앱 이벤트 데이터)의 생성 스크립트, 스키마, BigQuery 적재 절차를 설명합니다.

---

## 목차

1. [개요: 왜 합성 데이터인가](#1-개요-왜-합성-데이터인가)
2. [데이터 모델 개요](#2-데이터-모델-개요)
3. [테이블 스키마 상세](#3-테이블-스키마-상세)
   - [raw_users](#31-raw_users-사용자-프로필)
   - [raw_sessions](#32-raw_sessions-앱-세션)
   - [raw_events](#33-raw_events-이벤트-로그)
4. [비즈니스 맥락: 데이터 설계 의도](#4-비즈니스-맥락-데이터-설계-의도)
5. [합성 데이터 생성 스크립트](#5-합성-데이터-생성-스크립트)
   - [스크립트 구조](#51-스크립트-구조)
   - [핵심 파라미터](#52-핵심-파라미터)
   - [실행 방법](#53-실행-방법)
6. [BigQuery 적재 절차](#6-bigquery-적재-절차)
   - [방법 A: 스크립트 직접 적재](#61-방법-a-스크립트-직접-적재)
   - [방법 B: CSV → bq load](#62-방법-b-csv--bq-load)
   - [방법 C: Parquet → bq load](#63-방법-c-parquet--bq-load)
7. [BigQuery 스키마 DDL](#7-bigquery-스키마-ddl)
8. [비용 관리: On-Demand 환경에서 절약하기](#8-비용-관리-on-demand-환경에서-절약하기)
9. [데이터 검증](#9-데이터-검증)
10. [문제 해결](#10-문제-해결)

---

## 1. 개요: 왜 합성 데이터인가

코스 실습에 실제 사용자 데이터를 사용하면 개인정보 보호법(GDPR, PIPA) 문제가 발생합니다. 합성 데이터를 사용하면:

- **프라이버시 문제 없음**: 실제 사용자 정보가 포함되지 않음
- **재현 가능성**: 동일한 시드(seed)로 동일한 데이터 재생성 가능
- **실습 특화 설계**: DAU/MAU 분석에 의미 있는 패턴을 의도적으로 포함
- **비용 통제**: 데이터 규모를 조절하여 BigQuery on-demand 비용을 관리

### 시나리오 설명

**FitTrack**: 한국에서 서비스를 시작해 아시아 시장으로 확장 중인 B2C 모바일 피트니스 앱.

| 항목 | 내용 |
|------|------|
| 서비스 유형 | 워크아웃 트래킹, 목표 설정, 소셜 기능 |
| 주요 시장 | 한국(40%), 미국(25%), 일본(15%), 기타 아시아 |
| 플랫폼 | iOS(55%), Android(45%) |
| 구독 모델 | 무료(60%) / 프리미엄(30%) / 프리미엄 플러스(10%) |
| 분석 기간 | 2025년 1월 ~ 2026년 3월 (15개월) |

---

## 2. 데이터 모델 개요

```
raw_users (사용자 프로필)
    │
    ├── user_id (PK)
    │
    ├── raw_sessions (앱 세션)
    │       ├── session_id (PK)
    │       ├── user_id (FK → raw_users)
    │       └── ...
    │
    └── raw_events (이벤트 로그)
            ├── event_id (PK)
            ├── user_id (FK → raw_users)
            ├── session_id (FK → raw_sessions)
            └── ...
```

### 데이터 규모 (기본 설정)

| 테이블 | 행 수 | 예상 크기 |
|--------|-------|-----------|
| raw_users | ~10,000행 | ~2MB |
| raw_sessions | ~150,000행 | ~20MB |
| raw_events | ~500,000행 | ~80MB |

> **BigQuery on-demand 비용**: 총 데이터 크기 ~100MB. 조회 시 최소 10MB 과금 기준. 전체 스캔 기준 약 $0.0005 미만으로 실습 범위에서 사실상 무비용.

---

## 3. 테이블 스키마 상세

### 3.1 raw_users: 사용자 프로필

앱에 가입한 사용자 1명당 1행. 가입 시점의 디바이스/구독 정보와 인구통계 정보를 포함합니다.

| 컬럼명 | BigQuery 타입 | Nullable | 설명 |
|--------|--------------|----------|------|
| `user_id` | STRING | REQUIRED | 사용자 고유 식별자 (UUID v4) |
| `signup_timestamp` | TIMESTAMP | REQUIRED | 가입 시각 (UTC) |
| `signup_date` | DATE | REQUIRED | 가입 일자 (UTC 기준) |
| `country` | STRING | REQUIRED | 국가 코드 (ISO 3166-1 alpha-2: KR, US, JP, TW, TH, VN) |
| `language` | STRING | REQUIRED | 언어 코드 (ko, en, ja, zh-TW, th, vi) |
| `platform` | STRING | REQUIRED | 앱 플랫폼 (ios / android) |
| `device_type` | STRING | REQUIRED | 디바이스 유형 (smartphone / tablet) |
| `initial_app_version` | STRING | REQUIRED | 가입 시점 앱 버전 (semver: 3.0.5 ~ 3.2.1) |
| `subscription_tier` | STRING | REQUIRED | 구독 등급 (free / premium / premium_plus) |
| `age_group` | STRING | NULLABLE | 연령대 (18-24, 25-34, 35-44, 45-54, 55+). 10% 미입력 |
| `referral_source` | STRING | NULLABLE | 유입 채널 (organic, paid_search, social, referral). 5% 미입력 |
| `is_active` | BOOLEAN | REQUIRED | 활성 사용자 여부 |
| `last_active_date` | DATE | NULLABLE | 마지막 활동 일자 (세션 데이터에서 역산) |
| `_loaded_at` | TIMESTAMP | REQUIRED | 데이터 적재 시각 (dbt 소스 신선도 검사용) |

**분포 특성**:

```
국가:         KR(40%) > US(25%) > JP(15%) > TW(8%) > TH(7%) > VN(5%)
플랫폼:       iOS(55%) > Android(45%)  ← 한국 시장 반영
구독:         free(60%) > premium(30%) > premium_plus(10%)
유입 채널:    organic(40%) > paid_search(25%) > social(20%) > referral(15%)
연령대:       25-34(35%) > 35-44(25%) > 18-24(20%) > 45-54(12%) > 55+(8%)
```

---

### 3.2 raw_sessions: 앱 세션

사용자가 앱을 실행한 세션 1건당 1행. 세션 시작~종료 시간, 디바이스 정보, 이벤트 요약을 포함합니다.

| 컬럼명 | BigQuery 타입 | Nullable | 설명 |
|--------|--------------|----------|------|
| `session_id` | STRING | REQUIRED | 세션 고유 식별자 (UUID v4) |
| `user_id` | STRING | REQUIRED | 사용자 식별자 (raw_users.user_id 참조) |
| `session_start` | TIMESTAMP | REQUIRED | 세션 시작 시각 (UTC) |
| `session_end` | TIMESTAMP | NULLABLE | 세션 종료 시각 (UTC). NULL이면 비정상 종료 |
| `session_date` | DATE | REQUIRED | 세션 시작 일자 (UTC 기준, 파티션 키 권장) |
| `session_duration_seconds` | INT64 | NULLABLE | 세션 지속 시간 (초). 비정상 종료 시 NULL |
| `platform` | STRING | NULLABLE | 앱 플랫폼 (ios / android) |
| `app_version` | STRING | NULLABLE | 앱 버전 (semver: 3.0.5 ~ 3.2.1) |
| `device_model` | STRING | NULLABLE | 디바이스 모델명 (예: iPhone 16 Pro, Galaxy S25) |
| `os_version` | STRING | NULLABLE | OS 버전 (예: iOS 19.0, Android 16) |
| `ip_country` | STRING | NULLABLE | 접속 국가 코드 (IP 기반) |
| `event_count` | INT64 | REQUIRED | 세션 내 이벤트 수 |
| `screen_count` | INT64 | REQUIRED | 세션 내 화면 전환 수 (screen_view 이벤트 수. 이벤트 생성 후 역산) |
| `_loaded_at` | TIMESTAMP | REQUIRED | 데이터 적재 시각 |

**세션 특성**:

```
일평균 세션 수 (활성 사용자당): ~1.7회 (포아송 분포, 최대 5회)
세션 길이:     로그 정규 분포, 평균 ~8분, 최소 10초, 최대 2시간
비정상 종료:   ~3% (session_end IS NULL)
피크 시간:     오전 7~9시(KST), 오후 6~10시(KST)
주말 효과:     평일 대비 +17%
```

**iOS 디바이스 모델**: iPhone 16 Pro Max, iPhone 16 Pro, iPhone 16, iPhone 15 Pro Max, iPhone 15 Pro, iPhone 15, iPhone 14 Pro, iPhone 14, iPhone SE (3rd)

**Android 디바이스 모델**: Galaxy S25 Ultra, Galaxy S25, Galaxy S24 Ultra, Galaxy S24, Galaxy A55, Galaxy A35, Pixel 9 Pro, Pixel 9, Galaxy Z Flip 6, Galaxy Z Fold 6

---

### 3.3 raw_events: 이벤트 로그

앱 내 개별 사용자 행동 이벤트 1건당 1행. 가장 행 수가 많은 팩트 테이블.

| 컬럼명 | BigQuery 타입 | Nullable | 설명 |
|--------|--------------|----------|------|
| `event_id` | STRING | REQUIRED | 이벤트 고유 식별자 (UUID v4) |
| `user_id` | STRING | REQUIRED | 사용자 식별자 (raw_users.user_id 참조) |
| `session_id` | STRING | REQUIRED | 세션 식별자 (raw_sessions.session_id 참조) |
| `event_type` | STRING | REQUIRED | 이벤트 유형 (10가지 중 하나, 아래 참조) |
| `event_timestamp` | TIMESTAMP | REQUIRED | 이벤트 발생 시각 (UTC) |
| `event_date` | DATE | REQUIRED | 이벤트 발생 일자 (UTC 기준, 파티션 키 권장) |
| `platform` | STRING | REQUIRED | 앱 플랫폼 (ios / android) |
| `app_version` | STRING | REQUIRED | 앱 버전 (semver) |
| `device_model` | STRING | NULLABLE | 디바이스 모델명 |
| `event_properties` | JSON | NULLABLE | 이벤트별 추가 속성 (JSON 문자열) |
| `_loaded_at` | TIMESTAMP | REQUIRED | 데이터 적재 시각 |

**이벤트 유형 및 발생 비율**:

| event_type | 발생 비율 | event_properties 필드 |
|------------|----------|----------------------|
| `screen_view` | ~40% | `screen_name` (home, workout_list, workout_detail, profile, settings, social_feed, leaderboard, goals) |
| `app_open` | ~15% | 없음 |
| `app_close` | ~15% | 없음 |
| `push_notification_open` | ~9% | `notification_type` (workout_reminder, goal_progress, social_update, promotion) |
| `goal_set` | ~8% | `goal_type` (daily_steps, weekly_workouts, weight_target, streak_days) |
| `workout_start` | ~5% | `workout_type` (running, yoga, strength, cycling, stretching, hiit), `planned_duration_minutes` |
| `workout_complete` | ~4% | `actual_duration_minutes`, `calories_burned` |
| `social_share` | ~2% | `share_target` (kakao, instagram, twitter, facebook) |
| `purchase` | ~1.5% | `item_name` (premium_monthly, premium_annual, workout_pack, theme_bundle), `price_krw` |
| `goal_achieved` | ~0.5% | `goal_type`, `streak_count` |

**구매 가격 정보** (원화):

| item_name | price_krw |
|-----------|-----------|
| premium_monthly | 9,900원 |
| premium_annual | 79,900원 |
| workout_pack | 4,900원 |
| theme_bundle | 2,900원 |

---

## 4. 비즈니스 맥락: 데이터 설계 의도

합성 데이터는 단순히 랜덤 숫자가 아니라, 실제 B2C 앱에서 나타나는 **현실적인 패턴**을 시뮬레이션합니다. 아래 패턴들은 의도적으로 포함된 것으로, 분석 실습에서 의미 있는 인사이트를 도출할 수 있도록 설계되었습니다.

### 4.1 사용자 이탈 패턴 (Churn)

가입 후 90일이 경과하면 이탈 확률이 급격히 증가하는 시그모이드 패턴:

```
가입 7일 이내: 이탈 확률 낮음 (신규 유입)
가입 30일:    활발한 활동 구간
가입 90일:    이탈 변곡점 — 이 시점 이후 활동 확률 감소
가입 180일+:  비활성 전환 비율 증가
```

**분석 포인트**: 코호트 리텐션 분석에서 30일/60일/90일 리텐션율 변화를 관찰할 수 있습니다.

### 4.2 구독 등급별 행동 차이

유료 사용자는 무료 사용자 대비 더 활발한 활동을 보입니다:

```
free:          기본 활동 확률 × 0.8
premium:       기본 활동 확률 × 1.2
premium_plus:  기본 활동 확률 × 1.5
```

**분석 포인트**: 구독 등급별 DAU 기여율, 리텐션율 비교.

### 4.3 앱 버전 분포와 시간적 흐름

초기 가입자(2025년 1분기)는 구버전(3.0.5, 3.1.0), 최근 가입자(2025년 4분기 이후)는 신버전(3.2.0, 3.2.1) 사용 비율이 높습니다.

**분석 포인트**: 앱 버전 업그레이드에 따른 사용자 행동 변화, 강제 업데이트 효과.

### 4.4 시간대 패턴 (한국 기준)

```
오전 7~9시(KST):   출근 전 운동 피크
오후 12~13시(KST): 점심 시간 소폭 증가
오후 6~10시(KST):  퇴근 후 운동 메인 피크
주말:              전 시간대에 걸쳐 균등하게 +17%
```

### 4.5 소셜 공유 패턴

`social_share` 이벤트의 `share_target` 분포에는 한국 사용자 특성이 반영됩니다:

- **카카오(kakao)**: 한국 주요 메신저 — 국내 사용자에게 압도적 비율
- Instagram, Twitter, Facebook: 해외 사용자 비율 높음

---

## 5. 합성 데이터 생성 스크립트

스크립트 위치: `examples/generate_synthetic_data.py`

### 5.1 스크립트 구조

```
generate_synthetic_data.py
├── 상수 정의 (Constants)
│   ├── 기본 설정값 (DEFAULT_NUM_USERS, 날짜 범위, RANDOM_SEED)
│   ├── 분포 설정 (PLATFORM_WEIGHTS, COUNTRY_DISTRIBUTION, ...)
│   └── 이벤트 타입 및 가중치
│
├── 유틸리티 함수
│   ├── generate_uuid()    — 재현 가능한 UUID 생성
│   ├── weighted_choice()  — 가중치 기반 랜덤 선택
│   ├── compute_churn_probability()        — 이탈 확률 계산
│   └── compute_daily_activity_probability() — 일별 활동 확률 계산
│
├── SyntheticDataGenerator 클래스
│   ├── generate_all()         — 전체 데이터 생성 진입점
│   ├── _generate_users()      — raw_users 생성
│   ├── _generate_sessions()   — raw_sessions 생성
│   ├── _generate_events()     — raw_events 생성
│   ├── _derive_session_screen_count() — screen_count 역산
│   ├── save_to_csv()          — CSV 저장
│   ├── save_to_parquet()      — Parquet 저장
│   └── load_to_bigquery()     — BigQuery 직접 적재
│
└── main()  — CLI 인터페이스 (argparse)
```

### 5.2 핵심 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `--num-users` | 10,000 | 생성할 사용자 수 |
| `--start-date` | 2025-01-01 | 데이터 시작 날짜 |
| `--end-date` | 2026-03-31 | 데이터 종료 날짜 |
| `--seed` | 42 | 랜덤 시드 (재현성 보장) |
| `--events-per-session` | 8 | 세션당 평균 이벤트 수 |
| `--format` | csv | 출력 형식 (csv / parquet / both) |
| `--output-dir` | ./output | 파일 저장 경로 |
| `--load-to-bigquery` | (플래그) | BigQuery 직접 적재 활성화 |
| `--project-id` | (필수, BQ 적재 시) | GCP 프로젝트 ID |
| `--dataset` | raw | BigQuery 데이터셋 이름 |

### 5.3 실행 방법

#### 사전 준비

```bash
# uv로 가상환경 생성 및 의존성 설치
cd fittrack-analysis
uv sync

# 또는 pip 사용 시
pip install numpy pandas pyarrow google-cloud-bigquery pandas-gbq
```

#### 기본 실행 (CSV 파일 생성)

```bash
# 기본값으로 실행 (10,000명 사용자, 15개월 데이터)
python examples/generate_synthetic_data.py

# 출력 확인
ls -lh output/
# raw_users.csv    (~2MB)
# raw_sessions.csv (~20MB)
# raw_events.csv   (~80MB)
```

#### 규모 조정 (비용 관리)

```bash
# 소규모 테스트 (빠른 생성, 낮은 BQ 비용)
python examples/generate_synthetic_data.py \
    --num-users 1000 \
    --start-date 2025-10-01 \
    --end-date 2026-03-31

# 중간 규모 (권장 실습 환경)
python examples/generate_synthetic_data.py \
    --num-users 5000 \
    --start-date 2025-06-01 \
    --end-date 2026-03-31

# 전체 규모 (기본값 — 실제 분석 패턴 확인 시)
python examples/generate_synthetic_data.py
```

#### Parquet 형식으로 출력

```bash
# Parquet 형식 (BQ 적재 속도 빠름, 파일 크기 작음)
python examples/generate_synthetic_data.py --format parquet

# CSV + Parquet 모두 생성
python examples/generate_synthetic_data.py --format both
```

#### BigQuery 직접 적재

```bash
# 로컬에서 BQ 인증 후 직접 적재
gcloud auth application-default login

python examples/generate_synthetic_data.py \
    --load-to-bigquery \
    --project-id YOUR_GCP_PROJECT_ID \
    --dataset raw
```

---

## 6. BigQuery 적재 절차

BigQuery에 합성 데이터를 적재하는 방법은 세 가지입니다. 상황에 따라 선택하세요.

### 6.1 방법 A: 스크립트 직접 적재

**장점**: 가장 간단. 스키마 자동 적용.
**단점**: `google-cloud-bigquery` 패키지 필요. 로컬 인터넷 속도에 의존.

```bash
# 1. GCP 인증
gcloud auth application-default login

# 2. 환경변수 설정
export GCP_PROJECT_ID="your-project-id"

# 3. 데이터 생성 + BQ 적재 (한 번에)
python examples/generate_synthetic_data.py \
    --load-to-bigquery \
    --project-id $GCP_PROJECT_ID \
    --dataset raw

# 예상 출력:
# 🔄 사용자 데이터 생성 중...
#    ✅ 10,000명 사용자 생성 완료
# 🔄 세션 데이터 생성 중...
#    ✅ 148,523개 세션 생성 완료
# 🔄 이벤트 데이터 생성 중...
#    ✅ 498,241개 이벤트 생성 완료
# ⬆️  your-project.raw.raw_users 적재 중...
#    ✅ raw_users 적재 완료
# ...
```

### 6.2 방법 B: CSV → bq load

**장점**: `bq` CLI만 있으면 됨. 적재 작업을 명시적으로 확인 가능.
**단점**: 중간 단계(CSV 생성 → 업로드) 필요.

```bash
# 1. CSV 파일 생성
python examples/generate_synthetic_data.py --format csv --output-dir ./output

# 2. BQ 데이터셋 생성 (없는 경우)
bq --project_id=$GCP_PROJECT_ID mk \
    --dataset \
    --location=US \
    --description="FitTrack 모바일 앱 원시 데이터" \
    ${GCP_PROJECT_ID}:raw

# 3. raw_users 적재
bq load \
    --source_format=CSV \
    --skip_leading_rows=1 \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_users \
    ./output/raw_users.csv \
    user_id:STRING,signup_timestamp:TIMESTAMP,signup_date:DATE,\
country:STRING,language:STRING,platform:STRING,device_type:STRING,\
initial_app_version:STRING,subscription_tier:STRING,age_group:STRING,\
referral_source:STRING,is_active:BOOLEAN,last_active_date:DATE,\
_loaded_at:TIMESTAMP

# 4. raw_sessions 적재
bq load \
    --source_format=CSV \
    --skip_leading_rows=1 \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_sessions \
    ./output/raw_sessions.csv \
    session_id:STRING,user_id:STRING,session_start:TIMESTAMP,\
session_end:TIMESTAMP,session_date:DATE,session_duration_seconds:INTEGER,\
platform:STRING,app_version:STRING,device_model:STRING,os_version:STRING,\
ip_country:STRING,event_count:INTEGER,screen_count:INTEGER,\
_loaded_at:TIMESTAMP

# 5. raw_events 적재
bq load \
    --source_format=CSV \
    --skip_leading_rows=1 \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_events \
    ./output/raw_events.csv \
    event_id:STRING,user_id:STRING,session_id:STRING,event_type:STRING,\
event_timestamp:TIMESTAMP,event_date:DATE,platform:STRING,\
app_version:STRING,device_model:STRING,event_properties:JSON,\
_loaded_at:TIMESTAMP
```

### 6.3 방법 C: Parquet → bq load

**장점**: CSV 대비 파일 크기 작음(~60%), 적재 속도 빠름. 타입 정보 보존.
**단점**: `pyarrow` 패키지 필요.

```bash
# 1. Parquet 파일 생성
python examples/generate_synthetic_data.py --format parquet --output-dir ./output

# 2. BQ 적재 (스키마 자동 감지 가능)
bq load \
    --source_format=PARQUET \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_users \
    ./output/raw_users.parquet

bq load \
    --source_format=PARQUET \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_sessions \
    ./output/raw_sessions.parquet

bq load \
    --source_format=PARQUET \
    --replace \
    ${GCP_PROJECT_ID}:raw.raw_events \
    ./output/raw_events.parquet
```

---

## 7. BigQuery 스키마 DDL

스크립트 없이 직접 테이블을 생성하거나 스키마를 확인할 때 사용하세요.

### raw_users DDL

```sql
CREATE OR REPLACE TABLE `your_project.raw.raw_users`
(
  -- 식별자
  user_id             STRING    NOT NULL,

  -- 가입 정보
  signup_timestamp    TIMESTAMP NOT NULL,
  signup_date         DATE      NOT NULL,

  -- 인구통계 정보
  country             STRING    NOT NULL,  -- KR, US, JP, TW, TH, VN
  language            STRING    NOT NULL,  -- ko, en, ja, zh-TW, th, vi
  age_group           STRING,              -- 18-24, 25-34, 35-44, 45-54, 55+

  -- 디바이스 정보
  platform            STRING    NOT NULL,  -- ios, android
  device_type         STRING    NOT NULL,  -- smartphone, tablet
  initial_app_version STRING    NOT NULL,  -- 3.0.5 ~ 3.2.1

  -- 비즈니스 정보
  subscription_tier   STRING    NOT NULL,  -- free, premium, premium_plus
  referral_source     STRING,              -- organic, paid_search, social, referral

  -- 활동 상태 (세션 데이터에서 역산)
  is_active           BOOL      NOT NULL,
  last_active_date    DATE,

  -- 파이프라인 메타
  _loaded_at          TIMESTAMP NOT NULL
)
OPTIONS (
  description = 'FitTrack 모바일 앱 사용자 프로필 — 합성 데이터'
);
```

### raw_sessions DDL

```sql
CREATE OR REPLACE TABLE `your_project.raw.raw_sessions`
(
  -- 식별자
  session_id                STRING    NOT NULL,
  user_id                   STRING    NOT NULL,  -- raw_users.user_id 참조

  -- 세션 시간 정보
  session_start             TIMESTAMP NOT NULL,
  session_end               TIMESTAMP,           -- NULL: 비정상 종료
  session_date              DATE      NOT NULL,  -- 파티션 키로 사용 권장
  session_duration_seconds  INT64,               -- NULL: 비정상 종료

  -- 디바이스/앱 정보
  platform                  STRING,              -- ios, android
  app_version               STRING,              -- 3.0.5 ~ 3.2.1
  device_model              STRING,              -- 예: iPhone 16 Pro
  os_version                STRING,              -- 예: iOS 19.0
  ip_country                STRING,              -- IP 기반 국가 코드

  -- 이벤트 요약 (집계값)
  event_count               INT64     NOT NULL,  -- 세션 내 총 이벤트 수
  screen_count              INT64     NOT NULL,  -- screen_view 이벤트 수

  -- 파이프라인 메타
  _loaded_at                TIMESTAMP NOT NULL
)
PARTITION BY session_date
OPTIONS (
  description = 'FitTrack 모바일 앱 세션 기록 — 합성 데이터',
  partition_expiration_days = 730
);
```

### raw_events DDL

```sql
CREATE OR REPLACE TABLE `your_project.raw.raw_events`
(
  -- 식별자
  event_id          STRING    NOT NULL,
  user_id           STRING    NOT NULL,   -- raw_users.user_id 참조
  session_id        STRING    NOT NULL,   -- raw_sessions.session_id 참조

  -- 이벤트 정보
  event_type        STRING    NOT NULL,   -- app_open, screen_view, workout_start 등
  event_timestamp   TIMESTAMP NOT NULL,
  event_date        DATE      NOT NULL,   -- 파티션 키로 사용 권장

  -- 디바이스/앱 정보
  platform          STRING    NOT NULL,   -- ios, android
  app_version       STRING    NOT NULL,   -- semver
  device_model      STRING,

  -- 이벤트별 추가 속성 (이벤트 유형에 따라 구조 상이)
  event_properties  JSON,

  -- 파이프라인 메타
  _loaded_at        TIMESTAMP NOT NULL
)
PARTITION BY event_date
OPTIONS (
  description = 'FitTrack 모바일 앱 이벤트 로그 — 합성 데이터',
  partition_expiration_days = 730
);
```

---

## 8. 비용 관리: On-Demand 환경에서 절약하기

BigQuery on-demand 가격은 **조회 시 스캔한 데이터 바이트당 과금** ($6.25/TB)됩니다. 합성 데이터는 작지만, 올바른 습관을 들이는 것이 중요합니다.

### 8.1 데이터 규모별 예상 비용

| 사용자 수 | raw_events 크기 | 전체 스캔 비용 |
|----------|----------------|---------------|
| 1,000명 | ~8MB | $0.00005 미만 |
| 5,000명 | ~40MB | $0.00025 미만 |
| 10,000명 (기본) | ~80MB | $0.0005 미만 |

> BigQuery의 무료 쿼리 한도는 **월 1TB**입니다. 실습 범위에서는 한도를 초과할 가능성이 없습니다.

### 8.2 파티션 프루닝 활용

`raw_events`와 `raw_sessions`는 날짜 파티션으로 설계되었습니다. 쿼리 시 날짜 필터를 반드시 사용하세요:

```sql
-- ✅ 좋은 예: 파티션 프루닝 적용 (특정 기간만 스캔)
SELECT
  event_date,
  COUNT(DISTINCT user_id) AS dau
FROM `your_project.raw.raw_events`
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31'  -- 파티션 필터!
GROUP BY 1;

-- ❌ 나쁜 예: 전체 테이블 스캔
SELECT
  event_date,
  COUNT(DISTINCT user_id) AS dau
FROM `your_project.raw.raw_events`
GROUP BY 1;
```

### 8.3 SELECT * 지양

BigQuery는 선택한 컬럼 수에 따라 스캔 크기가 달라집니다 (컬럼형 스토리지):

```sql
-- ✅ 필요한 컬럼만 선택
SELECT event_id, user_id, event_type, event_date
FROM `your_project.raw.raw_events`
WHERE event_date = '2026-01-15';

-- ❌ 전체 컬럼 선택 (event_properties JSON 포함 → 크기 증가)
SELECT *
FROM `your_project.raw.raw_events`
WHERE event_date = '2026-01-15';
```

### 8.4 쿼리 실행 전 바이트 확인

BigQuery 콘솔에서 쿼리를 실행하기 전 우측 상단에 예상 처리 바이트가 표시됩니다. bq CLI에서는:

```bash
# dry_run으로 실제 실행 없이 처리 바이트만 확인
bq query \
    --use_legacy_sql=false \
    --dry_run \
    'SELECT COUNT(*) FROM `your_project.raw.raw_events` WHERE event_date = "2026-01-15"'
```

### 8.5 dbt 모델의 비용 최적화

dbt 스테이징 모델은 `view`로 설정되어 있습니다. dbt 실행 자체는 BQ 쿼리를 실행하지 않으며, 뷰를 참조할 때 스캔이 발생합니다.

mart 모델은 `table`로 materialized하여 반복 조회 비용을 절감합니다:

```yaml
# dbt_project.yml
models:
  fittrack:
    staging:
      +materialized: view      # 뷰: 저장 비용 없음
    marts:
      +materialized: table     # 테이블: 한 번 계산 후 재사용
```

---

## 9. 데이터 검증

적재 후 다음 쿼리로 데이터가 올바르게 들어갔는지 확인하세요.

### 9.1 행 수 확인

```sql
-- 각 테이블의 행 수 확인
SELECT 'raw_users'    AS table_name, COUNT(*) AS row_count FROM `your_project.raw.raw_users`
UNION ALL
SELECT 'raw_sessions' AS table_name, COUNT(*) AS row_count FROM `your_project.raw.raw_sessions`
UNION ALL
SELECT 'raw_events'   AS table_name, COUNT(*) AS row_count FROM `your_project.raw.raw_events`;
```

예상 결과 (기본값 10,000명):

| table_name | row_count |
|------------|-----------|
| raw_users | ~10,000 |
| raw_sessions | ~140,000~160,000 |
| raw_events | ~480,000~520,000 |

### 9.2 분포 확인

```sql
-- 국가별 사용자 분포
SELECT
  country,
  COUNT(*) AS user_count,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM `your_project.raw.raw_users`
GROUP BY country
ORDER BY user_count DESC;
```

예상 결과:

| country | pct |
|---------|-----|
| KR | ~40% |
| US | ~25% |
| JP | ~15% |
| TW | ~8% |
| TH | ~7% |
| VN | ~5% |

```sql
-- 이벤트 유형 분포
SELECT
  event_type,
  COUNT(*) AS event_count,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM `your_project.raw.raw_events`
GROUP BY event_type
ORDER BY event_count DESC;
```

### 9.3 참조 무결성 확인

```sql
-- raw_events에 raw_users에 없는 user_id가 있는지 확인
SELECT COUNT(*) AS orphan_events
FROM `your_project.raw.raw_events` e
LEFT JOIN `your_project.raw.raw_users` u USING (user_id)
WHERE u.user_id IS NULL;
-- 예상: 0

-- raw_events에 raw_sessions에 없는 session_id가 있는지 확인
SELECT COUNT(*) AS orphan_events
FROM `your_project.raw.raw_events` e
LEFT JOIN `your_project.raw.raw_sessions` s USING (session_id)
WHERE s.session_id IS NULL;
-- 예상: 0
```

### 9.4 DAU 간단 확인

```sql
-- 월별 평균 DAU 확인
SELECT
  FORMAT_DATE('%Y-%m', event_date) AS month,
  ROUND(AVG(dau), 0) AS avg_dau
FROM (
  SELECT
    event_date,
    COUNT(DISTINCT user_id) AS dau
  FROM `your_project.raw.raw_events`
  GROUP BY event_date
)
GROUP BY month
ORDER BY month;
```

---

## 10. 문제 해결

### 스크립트 실행 오류

**오류**: `ModuleNotFoundError: No module named 'numpy'`

```bash
# uv 환경에서 실행 중인지 확인
uv run python examples/generate_synthetic_data.py

# 또는 명시적으로 패키지 설치
uv add numpy pandas pyarrow
```

**오류**: `ModuleNotFoundError: No module named 'google.cloud.bigquery'`

```bash
# BigQuery 적재에 필요한 패키지 설치
uv add google-cloud-bigquery pandas-gbq
```

### BigQuery 적재 오류

**오류**: `google.api_core.exceptions.Forbidden: 403 Access Denied`

```bash
# 인증 상태 확인
gcloud auth list
gcloud auth application-default print-access-token

# 재인증
gcloud auth application-default login

# 서비스 계정 사용 시
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**오류**: `google.api_core.exceptions.NotFound: 404 Dataset not found`

```bash
# 데이터셋 먼저 생성
bq --project_id=$GCP_PROJECT_ID mk \
    --dataset \
    --location=US \
    ${GCP_PROJECT_ID}:raw
```

### 데이터 생성 속도

10,000명 기본 설정 시 예상 실행 시간:

| 단계 | 예상 시간 |
|------|-----------|
| 사용자 생성 | 5~10초 |
| 세션 생성 | 5~15분 (일별 반복 처리로 시간이 걸림) |
| 이벤트 생성 | 2~5분 |
| CSV 저장 | 10~30초 |
| BQ 적재 | 30~60초 |

> **팁**: 처음 실행 시 `--num-users 1000 --start-date 2025-10-01`로 소규모 테스트를 먼저 진행하세요. 약 5분 내에 완료됩니다.

### 세션 생성이 너무 느린 경우

세션 생성 루프는 `(일수) × (사용자 수)` 반복이므, 기간이 길수록 느려집니다.

```bash
# 기간을 줄여 빠르게 테스트
python examples/generate_synthetic_data.py \
    --num-users 2000 \
    --start-date 2026-01-01 \
    --end-date 2026-03-31  # 3개월만 생성
```

---

## 참고: dbt 소스와의 연결

합성 데이터를 BigQuery에 적재하면, `examples/dbt-models/staging/sources.yml`에 정의된 dbt 소스와 자동으로 연결됩니다:

```yaml
# sources.yml 발췌
sources:
  - name: mobile_app_raw
    database: "{{ env_var('BQ_PROJECT_ID') }}"
    schema: raw   # ← 합성 데이터 적재 위치와 일치
    tables:
      - name: raw_events
      - name: raw_users
      - name: raw_sessions
```

환경변수 설정 후 dbt를 실행하면 즉시 스테이징 모델을 빌드할 수 있습니다:

```bash
# 환경변수 설정
export BQ_PROJECT_ID="your-project-id"
export BQ_DATASET="analytics"  # mart 모델이 저장될 데이터셋

# dbt 실행
cd examples/dbt-models
dbt run --select staging
dbt test --select staging

# mart 모델까지 전체 실행
dbt run
dbt test
```

---

*이 가이드는 "하니스 엔지니어링 for 데이터 분석" 코스의 참고 자료입니다.*
*코스 메인 문서: [course-spec.md](../course-spec.md)*
*BigQuery 환경 설정: [gcp-bigquery-setup.md](./gcp-bigquery-setup.md)*
