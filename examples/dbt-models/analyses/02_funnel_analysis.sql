-- analyses/02_funnel_analysis.sql
-- 사용자 온보딩 & 기능 사용 퍼널 분석
--
-- ────────────────────────────────────────────────────────────────────────
-- 퍼널 분석이란?
-- ────────────────────────────────────────────────────────────────────────
-- 사용자가 목표(전환) 달성까지 거치는 단계별 이탈률을 측정합니다.
-- 각 단계에서 얼마나 많은 사용자가 빠져나가는지 파악하여
-- 제품 개선 우선순위를 결정하는 데 활용합니다.
--
-- 이 파일의 퍼널:
--   퍼널 1: 온보딩 퍼널 (가입 → 활성화 → 운동 완료 → 구독 전환)
--   퍼널 2: 운동 퍼널 (앱 오픈 → 운동 시작 → 운동 완료)
--   퍼널 3: 결제 퍼널 (DAU → 구매 페이지 조회 → 결제 완료)
--
-- 실행: dbt compile → BigQuery에서 직접 실행

-- ════════════════════════════════════════════════════════════════════════
-- 퍼널 1: 사용자 생애 온보딩 퍼널
-- ════════════════════════════════════════════════════════════════════════
-- 정의:
--   Step 1. 가입 (signup)            - 모든 사용자
--   Step 2. 활성화 (activated)        - 가입 후 7일 이내 첫 이벤트 발생
--   Step 3. 운동 완료 (first_workout)  - 최소 1번 운동 완료
--   Step 4. 유료 전환 (converted)     - 구독 등급이 premium/premium_plus

with user_funnel as (
    select
        user_id,
        signup_date_kst,
        subscription_tier,

        -- Step 2: 활성화 여부 (가입 후 7일 이내 첫 이벤트)
        is_activated,

        -- Step 3: 운동 완료 이력
        lifetime_workouts > 0                           as has_completed_workout,

        -- Step 4: 유료 구독 전환
        subscription_tier in ('premium', 'premium_plus') as is_paying

    from {{ ref('int_user_metrics') }}
),

-- 전체 사용자 수 (퍼널 분모)
total_users as (
    select count(distinct user_id) as total
    from user_funnel
),

-- 단계별 사용자 수 집계
funnel_counts as (
    select
        -- Step 1: 전체 가입자
        count(distinct user_id)                                             as step1_signup,

        -- Step 2: 활성화 사용자 (가입 후 7일 이내 이벤트)
        count(distinct case when is_activated then user_id end)             as step2_activated,

        -- Step 3: 운동 완료 경험 사용자
        count(distinct case when has_completed_workout then user_id end)    as step3_first_workout,

        -- Step 4: 유료 전환 사용자
        count(distinct case when is_paying then user_id end)                as step4_converted

    from user_funnel
)

select
    -- 단계별 사용자 수
    step1_signup,
    step2_activated,
    step3_first_workout,
    step4_converted,

    -- 단계별 전환율 (이전 단계 대비)
    round(safe_divide(step2_activated, step1_signup), 4)            as activation_rate,
    round(safe_divide(step3_first_workout, step2_activated), 4)     as workout_rate_from_activated,
    round(safe_divide(step4_converted, step3_first_workout), 4)     as conversion_rate_from_workout,

    -- 전체 대비 전환율 (Step 1 대비)
    round(safe_divide(step4_converted, step1_signup), 4)            as overall_conversion_rate,

    -- 각 단계 이탈자 수
    step1_signup - step2_activated                                  as drop_step1_to_2,
    step2_activated - step3_first_workout                           as drop_step2_to_3,
    step3_first_workout - step4_converted                           as drop_step3_to_4

from funnel_counts


-- ════════════════════════════════════════════════════════════════════════
-- 퍼널 2: 일별 운동 퍼널 (앱 오픈 → 운동 시작 → 운동 완료)
-- ════════════════════════════════════════════════════════════════════════
-- 목적: 운동 기능의 일별 drop-off 패턴 파악
--       "운동 시작률이 낮은가? 아니면 완료율이 낮은가?"

/*
select
    f.activity_date,
    f.dau                                               as step1_active_users,

    -- 운동 시작자 수 (workout_start 이벤트 발생)
    f.workout_users                                     as step2_workout_starters,

    -- 운동 완료자 수 (workout_complete 이벤트 발생)
    f.workout_completers                                as step3_workout_completers,

    -- 단계별 전환율
    f.workout_adoption_rate                             as step1_to_2_rate,  -- DAU 중 운동 시작 비율
    f.workout_completion_rate                           as step2_to_3_rate,  -- 시작 건 중 완료 비율

    -- 전체 운동 완료율 (DAU 기준)
    round(safe_divide(f.workout_completers, f.dau), 4)  as overall_workout_completion_rate,

    -- 요일 (주간 패턴 파악용)
    format_date('%A', f.activity_date)                  as day_of_week

from {{ ref('fct_feature_engagement') }} f
order by f.activity_date
*/


-- ════════════════════════════════════════════════════════════════════════
-- 퍼널 3: 유입 채널별 온보딩 퍼널 비교
-- ════════════════════════════════════════════════════════════════════════
-- 목적: 어느 유입 채널 사용자가 온보딩을 가장 잘 완료하는가?
--       마케팅 채널별 품질 비교 (CAC 대비 전환 효율)

/*
select
    referral_source,

    count(distinct user_id)                                                 as total_users,

    -- 활성화율 (채널별 온보딩 품질 지표)
    round(
        avg(case when is_activated then 1.0 else 0.0 end),
        4
    )                                                                       as activation_rate,

    -- 운동 완료율
    round(
        avg(case when lifetime_workouts > 0 then 1.0 else 0.0 end),
        4
    )                                                                       as workout_rate,

    -- 유료 전환율 (채널별 수익 기여도 핵심 지표)
    round(
        avg(case when subscription_tier in ('premium', 'premium_plus')
                 then 1.0 else 0.0 end),
        4
    )                                                                       as paid_conversion_rate,

    -- 1인당 평균 LTV
    round(avg(lifetime_revenue_krw), 0)                                     as avg_ltv_krw

from {{ ref('int_user_metrics') }}
group by referral_source
order by paid_conversion_rate desc
*/
