-- fct_daily_active_users.sql
-- DAU (일간 활성 사용자) 집계 마트 모델
-- 날짜별, 플랫폼별 활성 사용자 수와 주요 지표를 집계

{{ config(
    materialized='table',
    partition_by={
        'field': 'activity_date',
        'data_type': 'date',
        'granularity': 'day'
    },
    description='일간 활성 사용자(DAU) 집계. 날짜·플랫폼별 활성 사용자 수, 세션 수, 이벤트 수 포함.'
) }}

with daily_user_activity as (
    -- 날짜별 사용자 활동 요약
    select
        e.event_date_kst as activity_date,
        e.user_id,
        e.platform,

        -- 사용자별 일간 지표
        count(distinct e.session_id) as session_count,
        count(*) as event_count,
        min(e.event_timestamp_kst) as first_event_at,
        max(e.event_timestamp_kst) as last_event_at,
        -- 구매 이벤트의 매출 합산 (price_krw 컬럼, NULL이면 0)
        coalesce(sum(e.price_krw), 0) as daily_revenue
    from {{ ref('stg_events') }} e
    group by 1, 2, 3
),

-- 사용자 정보 조인 (유입 채널, 구독 등급)
enriched as (
    select
        a.*,
        u.referral_source,
        u.subscription_tier,
        u.signup_date_kst,
        -- 신규 사용자 여부 (가입 당일)
        a.activity_date = u.signup_date_kst as is_new_user
    from daily_user_activity a
    left join {{ ref('stg_users') }} u
        on a.user_id = u.user_id
),

-- 날짜·플랫폼별 DAU 집계
aggregated as (
    select
        activity_date,
        platform,

        -- DAU 핵심 지표
        count(distinct user_id) as dau,
        count(distinct case when is_new_user then user_id end) as new_users,
        count(distinct case when not is_new_user then user_id end) as returning_users,

        -- 참여도 지표
        sum(session_count) as total_sessions,
        sum(event_count) as total_events,
        avg(session_count) as avg_sessions_per_user,
        avg(event_count) as avg_events_per_user,

        -- 수익 지표 (구매 이벤트 매출 합산, 원 단위)
        sum(daily_revenue) as total_revenue,
        avg(daily_revenue) as avg_revenue_per_user,

        -- 유료 구독 사용자 비율 (premium + premium_plus)
        count(distinct case when subscription_tier in ('premium', 'premium_plus') then user_id end) as premium_dau,
        safe_divide(
            count(distinct case when subscription_tier in ('premium', 'premium_plus') then user_id end),
            count(distinct user_id)
        ) as premium_ratio

    from enriched
    group by 1, 2
)

select
    activity_date,
    platform,
    dau,
    new_users,
    returning_users,
    total_sessions,
    total_events,
    round(avg_sessions_per_user, 2) as avg_sessions_per_user,
    round(avg_events_per_user, 2) as avg_events_per_user,
    round(total_revenue, 2) as total_revenue,
    round(avg_revenue_per_user, 2) as avg_revenue_per_user,
    premium_dau,
    round(premium_ratio, 4) as premium_ratio
from aggregated
