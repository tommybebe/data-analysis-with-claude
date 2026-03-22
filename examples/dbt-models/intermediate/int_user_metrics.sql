-- int_user_metrics.sql
-- 중간 레이어: 사용자별 누적 지표 요약
-- 사용자의 전체 활동 기간에 걸친 집계 지표를 계산
-- 리텐션 분석, 사용자 세그멘테이션, LTV 추정에 활용

{{ config(
    materialized='view',
    description='''
        사용자별 누적 활동 지표.
        첫 이벤트 ~ 마지막 이벤트 기간의 행동 요약.
        코호트 리텐션 분석 및 사용자 세그멘테이션 마트에서 참조.
    '''
) }}

with daily_activity as (
    select * from {{ ref('int_user_daily_activity') }}
),

user_lifetime as (
    -- 사용자별 전체 기간 집계
    select
        user_id,

        -- 활동 기간
        min(activity_date)                                  as first_activity_date,
        max(activity_date)                                  as last_activity_date,
        count(distinct activity_date)                       as total_active_days,

        -- 전체 기간 이벤트 집계
        sum(total_events)                                   as lifetime_events,
        sum(session_count)                                  as lifetime_sessions,
        sum(workout_complete_count)                         as lifetime_workouts,
        sum(purchase_count)                                 as lifetime_purchases,
        sum(daily_revenue_krw)                              as lifetime_revenue_krw,

        -- 평균 일간 지표 (활동일 기준)
        avg(total_events)                                   as avg_daily_events,
        avg(total_session_duration_minutes)                 as avg_daily_session_minutes,
        avg(workout_completion_rate)                        as avg_workout_completion_rate,

        -- 피크 활동 지표
        max(total_events)                                   as max_daily_events,
        max(total_session_duration_minutes)                 as max_daily_session_minutes

    from daily_activity
    group by user_id
),

user_with_profile as (
    -- 사용자 프로필 정보 결합
    select
        l.*,
        u.signup_date_kst,
        u.days_since_signup,
        u.subscription_tier,
        u.referral_source,
        u.country,
        u.platform,
        u.age_group,

        -- 활성화 여부: 가입 후 첫 7일 이내 앱 오픈 여부로 정의
        date_diff(l.first_activity_date, u.signup_date_kst, day) <= 7
            as is_activated,

        -- 가입 후 첫 활동까지 소요 일수
        date_diff(l.first_activity_date, u.signup_date_kst, day)
            as days_to_first_activity,

        -- 최근 활동 이후 경과일 (이탈 지표)
        date_diff(
            current_date('Asia/Seoul'),
            l.last_activity_date,
            day
        )                                                   as days_since_last_activity

    from user_lifetime l
    left join {{ ref('stg_users') }} u
        on l.user_id = u.user_id
),

-- 사용자 세그먼트 분류 (간단한 RFM 기반)
segmented as (
    select
        *,

        -- 활동 빈도 세그먼트 (최근 30일 활동일 기준)
        case
            when days_since_last_activity > 30                then 'churned'      -- 30일 이상 미접속
            when total_active_days >= 20                      then 'power_user'   -- 월 20일 이상 활동
            when total_active_days >= 10                      then 'regular'      -- 월 10~19일 활동
            when total_active_days >= 3                       then 'casual'       -- 월 3~9일 활동
            else                                                   'dormant'      -- 3일 미만
        end                                                 as activity_segment,

        -- LTV 예측을 위한 수익 세그먼트
        case
            when lifetime_revenue_krw >= 100000               then 'high_value'
            when lifetime_revenue_krw >= 10000                then 'mid_value'
            when lifetime_revenue_krw > 0                     then 'low_value'
            else                                                   'non_paying'
        end                                                 as revenue_segment

    from user_with_profile
)

select * from segmented
