-- fct_monthly_active_users.sql
-- MAU (월간 활성 사용자) 집계 마트 모델
-- 월별, 플랫폼별 활성 사용자 수와 DAU/MAU 비율(stickiness) 계산

{{ config(
    materialized='table',
    partition_by={
        'field': 'activity_month',
        'data_type': 'date',
        'granularity': 'month'
    },
    description='월간 활성 사용자(MAU) 집계. DAU/MAU 비율(stickiness), 월간 수익 포함.'
) }}

with monthly_users as (
    -- 월별 고유 활성 사용자 집계
    select
        date_trunc(e.event_date_kst, month) as activity_month,
        e.platform,
        e.user_id,

        count(distinct e.event_date_kst) as active_days,
        count(distinct e.session_id) as monthly_sessions,
        count(*) as monthly_events,
        -- 구매 이벤트의 매출 합산 (price_krw 컬럼, NULL이면 0)
        coalesce(sum(e.price_krw), 0) as monthly_revenue
    from {{ ref('stg_events') }} e
    group by 1, 2, 3
),

-- 사용자 정보 보강
enriched as (
    select
        m.*,
        u.referral_source,
        u.subscription_tier,
        u.signup_date_kst,
        -- 해당 월에 가입한 신규 사용자 여부
        date_trunc(u.signup_date_kst, month) = m.activity_month as is_new_user_this_month
    from monthly_users m
    left join {{ ref('stg_users') }} u
        on m.user_id = u.user_id
),

-- 월별 DAU 평균 (stickiness 계산용)
daily_avg as (
    select
        date_trunc(activity_date, month) as activity_month,
        platform,
        avg(dau) as avg_daily_active_users
    from {{ ref('fct_daily_active_users') }}
    group by 1, 2
),

-- MAU 집계
aggregated as (
    select
        e.activity_month,
        e.platform,

        -- MAU 핵심 지표
        count(distinct e.user_id) as mau,
        count(distinct case when e.is_new_user_this_month then e.user_id end) as new_users,
        count(distinct case when not e.is_new_user_this_month then e.user_id end) as returning_users,

        -- 참여 깊이
        avg(e.active_days) as avg_active_days_per_user,
        avg(e.monthly_sessions) as avg_sessions_per_user,

        -- 수익
        sum(e.monthly_revenue) as total_revenue,

        -- 유료 구독 사용자 (premium + premium_plus)
        count(distinct case when e.subscription_tier in ('premium', 'premium_plus') then e.user_id end) as premium_mau,

        -- DAU/MAU 비율 (stickiness) — 사용자가 월 중 얼마나 자주 방문하는지
        d.avg_daily_active_users
    from enriched e
    left join daily_avg d
        on e.activity_month = d.activity_month
        and e.platform = d.platform
    group by 1, 2, d.avg_daily_active_users
)

select
    activity_month,
    platform,
    mau,
    new_users,
    returning_users,
    round(avg_active_days_per_user, 1) as avg_active_days_per_user,
    round(avg_sessions_per_user, 1) as avg_sessions_per_user,
    round(total_revenue, 2) as total_revenue,
    premium_mau,
    -- DAU/MAU stickiness (0~1, 높을수록 자주 방문)
    round(safe_divide(avg_daily_active_users, mau), 4) as stickiness,
    round(avg_daily_active_users, 0) as avg_dau
from aggregated
