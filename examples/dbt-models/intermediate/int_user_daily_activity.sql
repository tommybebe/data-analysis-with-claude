-- int_user_daily_activity.sql
-- 중간 레이어: 사용자-일자별 활동 집계
-- staging 이벤트 + 세션을 결합하여 사용자 단위의 일간 행동 요약 생성

{{ config(
    materialized='view',
    description='''
        사용자별 일간 활동 요약 (중간 집계).
        stg_events + stg_sessions를 결합하여 mart 레이어의 기반 데이터를 제공.
        DAU 마트, 리텐션 마트 등 여러 mart에서 공통으로 참조.
    '''
) }}

with event_summary as (
    -- 사용자-일자별 이벤트 집계
    select
        user_id,
        event_date_kst as activity_date,
        platform,

        -- 세션 및 이벤트 집계
        count(distinct session_id)                          as session_count,
        count(*)                                            as total_events,

        -- 이벤트 유형별 집계 (주요 행동 지표)
        countif(event_type = 'app_open')                   as app_open_count,
        countif(event_type = 'workout_start')              as workout_start_count,
        countif(event_type = 'workout_complete')           as workout_complete_count,
        countif(event_type = 'goal_set')                   as goal_set_count,
        countif(event_type = 'goal_achieved')              as goal_achieved_count,
        countif(event_type = 'purchase')                   as purchase_count,
        countif(event_type = 'social_share')               as social_share_count,

        -- 운동 완료율: 시작 대비 완료 비율 (NULL 안전 처리)
        safe_divide(
            countif(event_type = 'workout_complete'),
            nullif(countif(event_type = 'workout_start'), 0)
        )                                                   as workout_completion_rate,

        -- 수익 집계 (purchase 이벤트의 price_krw 합산)
        coalesce(
            sum(case when event_type = 'purchase' then price_krw end),
            0
        )                                                   as daily_revenue_krw,

        -- 첫/마지막 이벤트 시각
        min(event_timestamp_kst)                            as first_event_at,
        max(event_timestamp_kst)                            as last_event_at

    from {{ ref('stg_events') }}
    group by user_id, event_date_kst, platform
),

session_summary as (
    -- 사용자-일자별 세션 요약 (세션 길이, 비정상 종료율)
    select
        user_id,
        session_date_kst as activity_date,

        -- 세션 품질 지표
        avg(session_duration_minutes)                       as avg_session_duration_minutes,
        max(session_duration_minutes)                       as max_session_duration_minutes,
        sum(session_duration_minutes)                       as total_session_duration_minutes,

        -- 비정상 종료 비율
        safe_divide(
            countif(is_abnormal_exit),
            count(*)
        )                                                   as abnormal_exit_rate,

        avg(screen_count)                                   as avg_screens_per_session

    from {{ ref('stg_sessions') }}
    group by user_id, session_date_kst
),

-- 이벤트 요약과 세션 요약 결합
combined as (
    select
        e.user_id,
        e.activity_date,
        e.platform,

        -- 이벤트 기반 지표
        e.session_count,
        e.total_events,
        e.app_open_count,
        e.workout_start_count,
        e.workout_complete_count,
        e.goal_set_count,
        e.goal_achieved_count,
        e.purchase_count,
        e.social_share_count,
        e.workout_completion_rate,
        e.daily_revenue_krw,
        e.first_event_at,
        e.last_event_at,

        -- 세션 기반 지표 (NULL-safe: 세션 데이터 없을 경우 0/NULL 처리)
        coalesce(s.avg_session_duration_minutes, 0)         as avg_session_duration_minutes,
        coalesce(s.total_session_duration_minutes, 0)       as total_session_duration_minutes,
        s.max_session_duration_minutes,
        coalesce(s.abnormal_exit_rate, 0)                   as abnormal_exit_rate,
        coalesce(s.avg_screens_per_session, 0)              as avg_screens_per_session,

        -- 앱 사용 시간 기반 engagement score (간단 버전)
        -- 총 세션 시간(분) × 이벤트 수의 로그 스케일
        coalesce(s.total_session_duration_minutes, 0)
            * ln(e.total_events + 1)                        as engagement_score

    from event_summary e
    left join session_summary s
        on e.user_id = s.user_id
        and e.activity_date = s.activity_date
)

select * from combined
