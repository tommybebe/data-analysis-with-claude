-- intermediate/int_user_rolling_metrics.sql
-- 중간 레이어: 사용자별 롤링(이동) 지표 계산
--
-- ────────────────────────────────────────────────────────────────────────
-- 이 모델이 필요한 이유
-- ────────────────────────────────────────────────────────────────────────
-- int_user_daily_activity는 날짜별 개별 지표를 제공합니다.
-- 하지만 분석에서는 종종 "최근 N일간의 추세"가 필요합니다.
-- 예:
--   - "최근 7일 연속 활동한 사용자 (streak)"
--   - "최근 30일 운동 완료율 추세가 하락하는 사용자"
--   - "직전 주 대비 이번 주 참여도가 급감한 사용자 (이탈 조기 경고)"
--
-- 이 모델에서 다루는 윈도우 함수 패턴:
--   1. ROWS BETWEEN N PRECEDING AND CURRENT ROW  — 이동 집계
--   2. RANGE BETWEEN INTERVAL N DAY PRECEDING    — 날짜 범위 기반 집계
--   3. LAG / LEAD                               — 이전/이후 행 참조
--   4. FIRST_VALUE / LAST_VALUE                 — 윈도우 내 경계값
--
-- ⚠️  BigQuery 비용 주의:
--   이 모델은 사용자×날짜 조합이 많으면 스캔량이 큽니다.
--   VIEW로 구체화하되, mart에서 DATE 파티션 필터를 반드시 사용하세요.
--   예: WHERE activity_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)

{{ config(
    materialized='view',
    description='''
        사용자별 롤링(이동) 지표 계산.
        7일 이동 평균, 연속 활동 일수(streak), 주간 변화율을 제공.
        이탈 조기 경고, 재참여 트리거, 개인화 추천 엔진에서 참조.
        BigQuery에서 파티션 필터와 함께 사용 권장.
    '''
) }}

with daily_activity as (
    -- 기반 데이터: 사용자-일자별 활동 요약
    select
        user_id,
        activity_date,
        platform,
        total_events,
        session_count,
        workout_complete_count,
        workout_start_count,
        daily_revenue_krw,
        total_session_duration_minutes,
        engagement_score

    from {{ ref('int_user_daily_activity') }}
),

-- ─────────────────────────────────────────────────────────────────────
-- 패턴 1: 이동 평균 (Rolling Average)
-- 사용자별 최근 7일 활동 지표 평균
-- ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
-- ─────────────────────────────────────────────────────────────────────
rolling_avg as (
    select
        user_id,
        activity_date,
        platform,

        -- 원시 지표 (비교 기준)
        total_events,
        session_count,
        workout_complete_count,
        daily_revenue_krw,
        engagement_score,

        -- 7일 이동 평균: 단기 활동 추세
        -- 주의: 7일 미만 데이터가 있는 초기 구간은 가용 데이터 평균
        avg(total_events) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as events_7d_avg,

        avg(session_count) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as sessions_7d_avg,

        avg(total_session_duration_minutes) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as session_minutes_7d_avg,

        avg(engagement_score) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as engagement_7d_avg,

        -- 7일 누적 수익 (LTV 단기 추정)
        sum(daily_revenue_krw) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as revenue_7d_sum,

        -- 7일 누적 운동 완료 수
        sum(workout_complete_count) over (
            partition by user_id
            order by activity_date
            rows between 6 preceding and current row
        )                                               as workouts_7d_sum

    from daily_activity
),

-- ─────────────────────────────────────────────────────────────────────
-- 패턴 2: 이전 기간 대비 변화 (LAG)
-- 전주 동일 기간 대비 참여도 변화율 계산
-- ─────────────────────────────────────────────────────────────────────
with_lag as (
    select
        *,

        -- 전일 대비 참여도 변화
        engagement_score - lag(engagement_score) over (
            partition by user_id
            order by activity_date
        )                                               as engagement_day_over_day,

        -- 전주 동일 요일 대비 변화 (7행 이전 = 7일 전)
        -- 활동이 없던 날은 daily_activity에 행이 없으므로 NULL 가능
        engagement_score - lag(engagement_score, 7) over (
            partition by user_id
            order by activity_date
        )                                               as engagement_week_over_week,

        -- 활동이 있는 날 중 이전 활동일 (연속성 분석용)
        lag(activity_date) over (
            partition by user_id
            order by activity_date
        )                                               as prev_activity_date

    from rolling_avg
),

-- ─────────────────────────────────────────────────────────────────────
-- 패턴 3: 연속 활동 일수 (Streak)
-- 오늘 활동 직전까지 연속으로 활동한 날 수
-- 갭(전일 미활동)이 발생하면 streak 리셋
-- ─────────────────────────────────────────────────────────────────────
-- 구현 방법: "날짜 - ROW_NUMBER" 기법
-- ─────────────────────────────────────────────────────────────────────
-- 핵심 아이디어:
--   연속된 날짜는 하루씩 증가하고, ROW_NUMBER도 1씩 증가한다.
--   따라서 두 값의 차이(날짜의 숫자값 - row_number)는 연속 기간 내에서 일정하다.
--   gap이 발생하면 날짜가 2 이상 증가하지만 row_number는 1만 증가하므로 차이가 달라진다.
--
-- 예시:
--   2025-01-01 (9131일): row_number=1 → group_key = 9131 - 1 = 9130
--   2025-01-02 (9132일): row_number=2 → group_key = 9132 - 2 = 9130  ← 동일 그룹
--   2025-01-04 (9134일): row_number=3 → group_key = 9134 - 3 = 9131  ← 새 그룹 (gap!)
--
-- ⚠️ BigQuery 주의: 중첩 윈도우 함수(window function in PARTITION BY)는 지원하지 않음
--    이 "날짜 - row_number" 기법이 BigQuery에서 streak을 계산하는 표준 패턴
with_streak as (
    select
        *,

        -- 전일 활동 여부 플래그 (참고용)
        date_diff(activity_date, prev_activity_date, day) = 1
                                                        as is_consecutive,

        -- 연속 그룹 키: 날짜의 숫자값 - 사용자 내 row_number
        -- 같은 streak 구간의 행들은 동일한 streak_group_key를 가짐
        date_diff(activity_date, date '2000-01-01', day)
        - row_number() over (
            partition by user_id
            order by activity_date
          )                                             as streak_group_key

    from with_lag
),

-- 연속 활동 일수 계산: 동일 streak 그룹 내 몇 번째 날인지
streak_ranked as (
    select
        *,
        -- streak_group_key가 같은 행들 내에서의 순번 = 연속 활동 일수
        row_number() over (
            partition by user_id, streak_group_key
            order by activity_date
        )                                               as current_streak_days

    from with_streak
)

-- ─────────────────────────────────────────────────────────────────────
-- 최종 출력: 사용자-일자별 롤링 지표 통합
-- ─────────────────────────────────────────────────────────────────────
select
    user_id,
    activity_date,
    platform,

    -- 원시 당일 지표
    total_events,
    session_count,
    workout_complete_count,
    daily_revenue_krw,
    engagement_score,

    -- 7일 이동 평균 지표 (소수점 반올림)
    round(events_7d_avg, 1)                             as events_7d_avg,
    round(sessions_7d_avg, 2)                           as sessions_7d_avg,
    round(session_minutes_7d_avg, 1)                    as session_minutes_7d_avg,
    round(engagement_7d_avg, 2)                         as engagement_7d_avg,
    round(revenue_7d_sum, 0)                            as revenue_7d_sum,
    workouts_7d_sum,

    -- 변화율 지표 (이탈 감지, 재참여 타이밍 결정)
    round(engagement_day_over_day, 2)                   as engagement_dod,
    round(engagement_week_over_week, 2)                 as engagement_wow,

    -- 참여도 추세 라벨 (이탈 위험 조기 경고)
    case
        -- 전주 대비 50% 이상 하락: 이탈 위험
        when engagement_week_over_week < -(engagement_7d_avg * 0.5)
            then 'at_risk'
        -- 전주 대비 20% 이상 상승: 활성화 중
        when engagement_week_over_week > (engagement_7d_avg * 0.2)
            then 'growing'
        -- 안정적
        else 'stable'
    end                                                 as engagement_trend,

    -- 연속 활동 일수 (streak gamification, 알림 트리거)
    current_streak_days,

    -- 연속 활동 상태 라벨
    case
        when current_streak_days >= 30  then 'champion'    -- 30일 이상
        when current_streak_days >= 7   then 'on_fire'     -- 7일 이상
        when current_streak_days >= 3   then 'building'    -- 3일 이상
        else                                 'starting'    -- 3일 미만
    end                                                 as streak_label,

    -- 이전 활동일 (재방문 간격 계산용)
    prev_activity_date,
    date_diff(activity_date, prev_activity_date, day)   as days_since_prev_activity

from streak_ranked
