-- fct_revenue_analysis.sql
-- 수익·monetization 분석 마트
-- 구독 등급별, 유입 채널별, 국가별 월간 수익 현황 집계
--
-- 분석 활용 예시:
--   - 구독 등급(free/premium/premium_plus)별 ARPU와 결제 전환율 추이
--   - 어느 유입 채널이 가장 높은 수익을 창출하는가? (마케팅 ROI 분석)
--   - 국가별 결제 사용자 비율 차이 (시장별 monetization 전략 수립)
--   - 월간 신규 vs 기존 결제 사용자 수익 기여도 비교

{{ config(
    materialized='table',
    partition_by={
        'field': 'activity_month',
        'data_type': 'date',
        'granularity': 'month'
    },
    description='''
        월간 수익 분석 팩트 테이블.
        구독 등급·유입 채널별 MAU, ARPU, ARPPU, 결제 전환율 제공.
        LTV 추정, 마케팅 ROI 분석, 구독 전환 최적화에 활용.
    '''
) }}

with monthly_events as (
    -- 월별 활성 사용자 이벤트 (MAU 집계 기반)
    select
        date_trunc(event_date_kst, month)       as activity_month,
        user_id,
        -- 구매 이벤트 수 및 금액 집계
        countif(event_type = 'purchase')        as purchase_count,
        sum(
            case when event_type = 'purchase'
                 then coalesce(price_krw, 0)
            end
        )                                       as monthly_revenue_krw
    from {{ ref('stg_events') }}
    group by 1, 2
),

-- 사용자 프로필 정보 결합
user_monthly as (
    select
        m.activity_month,
        m.user_id,
        m.purchase_count,
        coalesce(m.monthly_revenue_krw, 0)      as monthly_revenue_krw,
        -- 결제 여부 플래그 (purchase 이벤트 1건 이상)
        m.purchase_count > 0                    as is_paying,
        u.subscription_tier,
        u.referral_source,
        u.country,
        u.platform,
        u.signup_date_kst,
        -- 신규 사용자 여부: 해당 월에 가입
        date_trunc(u.signup_date_kst, month) = m.activity_month
                                                as is_new_user_this_month
    from monthly_events m
    left join {{ ref('stg_users') }} u
        on m.user_id = u.user_id
),

-- ── 구독 등급별 집계 ────────────────────────────────────────────────────
tier_summary as (
    select
        activity_month,
        subscription_tier,
        'subscription_tier'                                 as breakdown_dimension,
        subscription_tier                                   as breakdown_value,

        count(distinct user_id)                             as mau,
        count(distinct case when is_new_user_this_month
                            then user_id end)               as new_mau,
        count(distinct case when not is_new_user_this_month
                            then user_id end)               as returning_mau,

        -- 결제 사용자 수
        count(distinct case when is_paying then user_id end) as paying_users,

        -- 총 수익 (원화)
        sum(monthly_revenue_krw)                            as total_revenue_krw,
        sum(purchase_count)                                 as total_purchases,

        -- ARPU: 전체 MAU 기준 1인당 평균 수익
        -- 마케팅 투자 효율성 측정에 사용
        safe_divide(
            sum(monthly_revenue_krw),
            count(distinct user_id)
        )                                                   as arpu_krw,

        -- ARPPU: 결제 사용자 기준 1인당 평균 수익
        -- 결제 사용자 가치 측정에 사용
        safe_divide(
            sum(monthly_revenue_krw),
            count(distinct case when is_paying then user_id end)
        )                                                   as arppu_krw,

        -- 결제 전환율: MAU 중 실제 결제한 비율
        safe_divide(
            count(distinct case when is_paying then user_id end),
            count(distinct user_id)
        )                                                   as payment_conversion_rate

    from user_monthly
    group by 1, 2, 3, 4
),

-- ── 유입 채널별 집계 ────────────────────────────────────────────────────
channel_summary as (
    select
        activity_month,
        null                                                as subscription_tier,
        'referral_source'                                   as breakdown_dimension,
        coalesce(referral_source, 'unknown')                as breakdown_value,

        count(distinct user_id)                             as mau,
        count(distinct case when is_new_user_this_month
                            then user_id end)               as new_mau,
        count(distinct case when not is_new_user_this_month
                            then user_id end)               as returning_mau,

        count(distinct case when is_paying then user_id end) as paying_users,
        sum(monthly_revenue_krw)                            as total_revenue_krw,
        sum(purchase_count)                                 as total_purchases,

        safe_divide(
            sum(monthly_revenue_krw),
            count(distinct user_id)
        )                                                   as arpu_krw,

        safe_divide(
            sum(monthly_revenue_krw),
            count(distinct case when is_paying then user_id end)
        )                                                   as arppu_krw,

        safe_divide(
            count(distinct case when is_paying then user_id end),
            count(distinct user_id)
        )                                                   as payment_conversion_rate

    from user_monthly
    group by 1, 2, 3, 4
)

-- 구독 등급별 집계 출력
-- (유입 채널별 분석이 필요한 경우 channel_summary CTE를 별도로 조회)
select
    activity_month,
    subscription_tier,
    mau,
    new_mau,
    returning_mau,
    paying_users,
    round(total_revenue_krw, 0)                             as total_revenue_krw,
    total_purchases,
    round(arpu_krw, 0)                                      as arpu_krw,
    round(arppu_krw, 0)                                     as arppu_krw,
    round(payment_conversion_rate, 4)                       as payment_conversion_rate,

    -- 신규 사용자 비율 (획득 효율 지표)
    round(safe_divide(new_mau, mau), 4)                     as new_user_ratio,

    -- 구독 등급별 수익 기여도 (동일 월 내 비율, 윈도우 함수)
    round(
        safe_divide(
            total_revenue_krw,
            sum(total_revenue_krw) over (partition by activity_month)
        ),
        4
    )                                                       as revenue_share_of_month

from tier_summary
