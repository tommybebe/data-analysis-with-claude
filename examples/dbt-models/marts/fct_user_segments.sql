-- fct_user_segments.sql
-- 사용자 세그먼트 스냅샷 마트
-- int_user_metrics의 세그멘테이션 결과를 분석 가능한 집계 형태로 노출
--
-- 분석 활용 예시:
--   - 현재 파워 유저 / 일반 / 이탈 위험 사용자 분포는?
--   - 유입 채널별 세그먼트 구성 비율 비교 (채널 품질 평가)
--   - 구독 등급×세그먼트 교차 분석 (업셀링 기회 발굴)
--   - 세그먼트별 평균 LTV, 세션 시간, 운동 완료율 비교
--
-- 주의: 이 모델은 실행 시점의 스냅샷.
--       시계열 세그먼트 변화 추적은 Snapshot 기능을 별도로 사용.

{{ config(
    materialized='table',
    description='''
        사용자 세그먼트 집계 스냅샷.
        activity_segment(power_user/regular/casual/dormant/churned)와
        revenue_segment(high_value/mid_value/low_value/non_paying) 기준으로
        사용자 분포, 행동 지표, 수익 지표를 집계.
        대시보드 세그먼트 현황판 및 타겟 마케팅 캠페인 구성에 활용.
    '''
) }}

with user_metrics as (
    -- 사용자별 누적 지표 + 세그먼트 분류 (중간 레이어 참조)
    select * from {{ ref('int_user_metrics') }}
),

-- ── 세그먼트 교차 집계 ─────────────────────────────────────────────────
-- activity_segment × revenue_segment 조합별 사용자 분포와 주요 지표
segment_cross as (
    select
        activity_segment,
        revenue_segment,
        subscription_tier,
        referral_source,
        country,
        platform,

        -- 세그먼트별 사용자 수
        count(distinct user_id)                             as user_count,

        -- ── 활동 행동 지표 ──────────────────────────────────────────
        -- 전체 활동 일수 (앱 사용 깊이)
        avg(total_active_days)                              as avg_active_days,
        -- 가입 이후 경과일 대비 활동일 비율 (활동 밀도)
        avg(
            safe_divide(total_active_days, nullif(days_since_signup, 0))
        )                                                   as avg_activity_density,
        avg(avg_daily_session_minutes)                      as avg_daily_session_minutes,
        avg(lifetime_workouts)                              as avg_lifetime_workouts,
        avg(avg_workout_completion_rate)                    as avg_workout_completion_rate,

        -- ── 수익 지표 ──────────────────────────────────────────────
        -- 세그먼트 내 결제 이력이 있는 사용자 비율
        avg(case when lifetime_revenue_krw > 0 then 1.0 else 0.0 end)
                                                            as paying_user_rate,
        avg(lifetime_revenue_krw)                           as avg_ltv_krw,
        sum(lifetime_revenue_krw)                           as total_ltv_krw,
        max(lifetime_revenue_krw)                           as max_ltv_krw,

        -- ── 활성화 지표 ────────────────────────────────────────────
        -- 가입 후 7일 이내 첫 이벤트 발생 비율 (온보딩 성공률)
        avg(case when is_activated then 1.0 else 0.0 end)  as activation_rate,
        avg(days_to_first_activity)                         as avg_days_to_first_activity,

        -- ── 이탈 위험 지표 ─────────────────────────────────────────
        avg(days_since_last_activity)                       as avg_days_since_last_activity

    from user_metrics
    group by
        activity_segment,
        revenue_segment,
        subscription_tier,
        referral_source,
        country,
        platform
),

-- ── 전체 사용자 수 (비율 계산용) ───────────────────────────────────────
total_users as (
    select count(distinct user_id) as total_count
    from user_metrics
)

select
    s.activity_segment,
    s.revenue_segment,
    s.subscription_tier,
    s.referral_source,
    s.country,
    s.platform,

    -- 사용자 수 및 비율
    s.user_count,
    round(
        safe_divide(s.user_count, t.total_count),
        4
    )                                                       as user_share,

    -- 활동 행동 지표 (반올림)
    round(s.avg_active_days, 1)                             as avg_active_days,
    round(s.avg_activity_density, 4)                        as avg_activity_density,
    round(s.avg_daily_session_minutes, 1)                   as avg_daily_session_minutes,
    round(s.avg_lifetime_workouts, 1)                       as avg_lifetime_workouts,
    round(s.avg_workout_completion_rate, 4)                 as avg_workout_completion_rate,

    -- 수익 지표 (반올림)
    round(s.paying_user_rate, 4)                            as paying_user_rate,
    round(s.avg_ltv_krw, 0)                                 as avg_ltv_krw,
    round(s.total_ltv_krw, 0)                               as total_ltv_krw,
    round(s.max_ltv_krw, 0)                                 as max_ltv_krw,

    -- 활성화 지표 (반올림)
    round(s.activation_rate, 4)                             as activation_rate,
    round(s.avg_days_to_first_activity, 1)                  as avg_days_to_first_activity,

    -- 이탈 위험 지표 (반올림)
    round(s.avg_days_since_last_activity, 1)                as avg_days_since_last_activity,

    -- 재참여 우선순위 점수 (높을수록 재참여 마케팅 우선 대상)
    -- 공식: avg_ltv_krw가 높고(가치 있음) days_since_last_activity가 크면(이탈 위험) 높은 점수
    round(
        safe_divide(s.avg_ltv_krw, 1000.0)
            * ln(greatest(s.avg_days_since_last_activity, 1) + 1),
        2
    )                                                       as reengagement_priority_score

from segment_cross s
cross join total_users t
