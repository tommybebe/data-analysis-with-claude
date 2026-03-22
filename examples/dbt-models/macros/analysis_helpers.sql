-- macros/analysis_helpers.sql
-- 데이터 분석 공통 매크로 모음
-- 반복적으로 사용되는 BigQuery 분석 패턴을 매크로로 추상화
--
-- 활용 예시:
--   {{ utc_to_kst('event_timestamp') }}      → KST 타임스탬프 변환
--   {{ safe_rate('completes', 'starts') }}   → NULL-safe 비율 계산
--   {{ date_spine_last_n_days(30) }}         → 최근 N일 날짜 목록 생성


-- ============================================================
-- utc_to_kst: UTC 타임스탬프 → KST(UTC+9) 변환
-- ============================================================
-- 사용 예: select {{ utc_to_kst('event_timestamp') }} as event_timestamp_kst
-- BigQuery에서 TIMESTAMP → KST DATETIME 변환 후 다시 TIMESTAMP로 캐스트
{% macro utc_to_kst(timestamp_col) %}
    timestamp(datetime({{ timestamp_col }}, 'Asia/Seoul'))
{% endmacro %}


-- ============================================================
-- utc_to_kst_date: UTC 타임스탬프 → KST 기준 DATE 추출
-- ============================================================
-- 사용 예: select {{ utc_to_kst_date('event_timestamp') }} as event_date_kst
-- DAU/MAU 집계 시 KST 기준 날짜 파티션 키 생성에 사용
{% macro utc_to_kst_date(timestamp_col) %}
    date(datetime({{ timestamp_col }}, 'Asia/Seoul'))
{% endmacro %}


-- ============================================================
-- safe_rate: NULL-safe 비율 계산 (분자 / 분모)
-- ============================================================
-- 사용 예: {{ safe_rate('workout_complete_count', 'workout_start_count') }}
-- 분모가 0이거나 NULL인 경우 NULL 반환 (0으로 나누기 오류 방지)
-- BigQuery의 SAFE_DIVIDE 래퍼
{% macro safe_rate(numerator, denominator, round_digits=4) %}
    round(
        safe_divide({{ numerator }}, nullif({{ denominator }}, 0)),
        {{ round_digits }}
    )
{% endmacro %}


-- ============================================================
-- event_count: 특정 이벤트 유형 집계
-- ============================================================
-- 사용 예: {{ event_count('workout_start') }} as workout_start_count
-- stg_events 기반 모델에서 COUNTIF 패턴 단순화
{% macro event_count(event_type_value) %}
    countif(event_type = '{{ event_type_value }}')
{% endmacro %}


-- ============================================================
-- revenue_sum: 구매 이벤트의 수익 합산 (NULL → 0 처리)
-- ============================================================
-- 사용 예: {{ revenue_sum() }} as daily_revenue_krw
-- 구매 이벤트의 price_krw 합산, 구매 없는 날은 0 반환
{% macro revenue_sum(event_type_col='event_type', price_col='price_krw') %}
    coalesce(
        sum(case when {{ event_type_col }} = 'purchase' then {{ price_col }} end),
        0
    )
{% endmacro %}


-- ============================================================
-- activity_segment_label: 활동 세그먼트 분류 CASE WHEN
-- ============================================================
-- 사용 예: {{ activity_segment_label('total_active_days', 'days_since_last_activity') }}
-- int_user_metrics와 동일한 세그멘테이션 로직을 재사용 가능하게 추상화
-- 기준값은 vars로 오버라이드 가능 (dbt_project.yml에서 설정)
{% macro activity_segment_label(active_days_col, days_since_last_col) %}
    case
        -- 30일 이상 미접속: 이탈 사용자
        when {{ days_since_last_col }} > 30
            then 'churned'
        -- 월 20일 이상 활동: 파워 유저
        when {{ active_days_col }} >= 20
            then 'power_user'
        -- 월 10~19일 활동: 일반 사용자
        when {{ active_days_col }} >= 10
            then 'regular'
        -- 월 3~9일 활동: 가벼운 사용자
        when {{ active_days_col }} >= 3
            then 'casual'
        -- 3일 미만 활동: 휴면 사용자
        else 'dormant'
    end
{% endmacro %}


-- ============================================================
-- revenue_segment_label: 수익 세그먼트 분류 CASE WHEN
-- ============================================================
-- 사용 예: {{ revenue_segment_label('lifetime_revenue_krw') }}
-- LTV 기반 사용자 가치 등급 분류
{% macro revenue_segment_label(revenue_col) %}
    case
        when {{ revenue_col }} >= 100000  then 'high_value'    -- 누적 10만원 이상
        when {{ revenue_col }} >= 10000   then 'mid_value'     -- 누적 1만원 이상
        when {{ revenue_col }} > 0        then 'low_value'     -- 소액 구매 이력
        else                                   'non_paying'    -- 구매 이력 없음
    end
{% endmacro %}
