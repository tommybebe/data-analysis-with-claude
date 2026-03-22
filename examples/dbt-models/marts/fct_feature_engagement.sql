-- fct_feature_engagement.sql
-- 기능별 참여도 분석 마트
-- 운동, 목표 설정, 소셜 공유 등 핵심 기능의 일별 사용 현황 집계
--
-- 분석 활용 예시:
--   - 어떤 기능이 사용자 참여를 가장 많이 이끌어내는가?
--   - 운동 시작 → 완료 funnel의 일별 drop-off 추이는?
--   - 소셜 공유 기능이 활성화된 날의 신규 유입 효과는?

{{ config(
    materialized='table',
    partition_by={
        'field': 'activity_date',
        'data_type': 'date',
        'granularity': 'day'
    },
    cluster_by=['activity_date'],
    description='''
        기능별 일간 참여도 팩트 테이블.
        운동·목표·소셜·구매 기능의 채택률(adoption_rate)과 완료율(completion_rate)을 날짜별 집계.
        기능 우선순위 결정, A/B 테스트 평가, 제품 개선 방향 도출에 활용.
    '''
) }}

with daily_activity as (
    -- 사용자-일자별 기능 사용 요약 (중간 레이어 참조)
    select * from {{ ref('int_user_daily_activity') }}
),

-- 날짜별 DAU 산출 (채택률 분모)
daily_dau as (
    select
        activity_date,
        count(distinct user_id) as dau
    from daily_activity
    group by activity_date
),

-- 날짜별 기능 참여 집계
feature_metrics as (
    select
        a.activity_date,

        -- ── 운동 기능 (핵심 가치 기능) ──────────────────────────────
        -- 운동을 1회 이상 시작한 사용자 수
        countif(a.workout_start_count > 0)                  as workout_users,
        -- 운동을 1회 이상 완료한 사용자 수 (완주율 분자)
        countif(a.workout_complete_count > 0)               as workout_completers,
        sum(a.workout_start_count)                          as total_workout_starts,
        sum(a.workout_complete_count)                       as total_workout_completes,

        -- ── 목표 설정 기능 ────────────────────────────────────────────
        -- 목표를 1개 이상 설정한 사용자
        countif(a.goal_set_count > 0)                       as goal_setters,
        -- 목표를 1개 이상 달성한 사용자
        countif(a.goal_achieved_count > 0)                  as goal_achievers,
        sum(a.goal_set_count)                               as total_goals_set,
        sum(a.goal_achieved_count)                          as total_goals_achieved,

        -- ── 소셜 공유 기능 ────────────────────────────────────────────
        -- 1회 이상 공유한 사용자 (바이럴 루프 기여자)
        countif(a.social_share_count > 0)                   as social_sharers,
        sum(a.social_share_count)                           as total_shares,

        -- ── 구매/결제 기능 ────────────────────────────────────────────
        countif(a.purchase_count > 0)                       as purchasers,
        sum(a.purchase_count)                               as total_purchases,
        sum(a.daily_revenue_krw)                            as total_revenue_krw

    from daily_activity a
    group by a.activity_date
)

select
    f.activity_date,

    -- DAU (모든 비율의 분모)
    d.dau,

    -- ── 운동 기능 원시 수치 ──────────────────────────────────────────
    f.workout_users,
    f.workout_completers,
    f.total_workout_starts,
    f.total_workout_completes,

    -- 운동 채택률: 당일 DAU 중 운동을 시작한 비율 (0~1)
    -- 기준값: 0.30 이상이면 핵심 기능으로서 건강한 수준
    round(safe_divide(f.workout_users, d.dau), 4)           as workout_adoption_rate,

    -- 운동 완료율: 시작 건수 대비 완료 건수 (funnel drop-off 지표)
    -- 낮은 값 → 운동 프로그램 난이도/길이 재검토 신호
    round(
        safe_divide(f.total_workout_completes, nullif(f.total_workout_starts, 0)),
        4
    )                                                       as workout_completion_rate,

    -- ── 목표 기능 원시 수치 ──────────────────────────────────────────
    f.goal_setters,
    f.goal_achievers,
    f.total_goals_set,
    f.total_goals_achieved,

    -- 목표 기능 채택률
    round(safe_divide(f.goal_setters, d.dau), 4)            as goal_adoption_rate,

    -- 목표 달성률: 설정된 목표 중 달성된 비율
    round(
        safe_divide(f.total_goals_achieved, nullif(f.total_goals_set, 0)),
        4
    )                                                       as goal_achievement_rate,

    -- ── 소셜 기능 원시 수치 ──────────────────────────────────────────
    f.social_sharers,
    f.total_shares,

    -- 소셜 기능 채택률 (바이럴 계수 추정의 선행 지표)
    round(safe_divide(f.social_sharers, d.dau), 4)          as social_adoption_rate,

    -- 공유자당 평균 공유 횟수
    round(
        safe_divide(f.total_shares, nullif(f.social_sharers, 0)),
        2
    )                                                       as avg_shares_per_sharer,

    -- ── 구매/결제 원시 수치 ──────────────────────────────────────────
    f.purchasers,
    f.total_purchases,
    round(f.total_revenue_krw, 0)                           as total_revenue_krw,

    -- 일간 결제 전환율 (DAU 대비 구매자 비율)
    round(safe_divide(f.purchasers, d.dau), 4)              as purchase_conversion_rate,

    -- 구매자당 평균 결제 금액 (ARPPU 일간 추정치)
    round(
        safe_divide(f.total_revenue_krw, nullif(f.purchasers, 0)),
        0
    )                                                       as revenue_per_purchaser_krw

from feature_metrics f
inner join daily_dau d
    on f.activity_date = d.activity_date
