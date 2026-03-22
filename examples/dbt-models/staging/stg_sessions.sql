-- stg_sessions.sql
-- 세션 데이터 스테이징 모델
-- 세션 정리, 비정상 종료 처리, 세션 길이 계산

{{ config(
    materialized='view',
    description='정리된 세션 데이터. 비정상 종료 처리, 세션 길이(분) 계산.'
) }}

with source as (
    select * from {{ source('mobile_app_raw', 'raw_sessions') }}
),

transformed as (
    select
        session_id,
        user_id,

        session_start,
        date(datetime(session_start, 'Asia/Seoul')) as session_date_kst,

        -- 비정상 종료 처리: session_end가 NULL이면 session_start + 5분으로 대체
        coalesce(
            session_end,
            timestamp_add(session_start, interval 5 minute)
        ) as session_end,

        -- 비정상 종료 플래그
        session_end is null as is_abnormal_exit,

        -- 세션 길이: 원본 duration 또는 계산된 값 (분 단위)
        coalesce(
            session_duration_seconds / 60.0,
            timestamp_diff(
                coalesce(session_end, timestamp_add(session_start, interval 5 minute)),
                session_start,
                second
            ) / 60.0
        ) as session_duration_minutes,

        event_count,
        screen_count,
        platform,
        app_version,
        device_model,
        os_version,
        ip_country,

        _loaded_at
    from source
    where
        session_id is not null
        and user_id is not null
        and session_start is not null
        -- 세션 시작이 미래가 아닌 경우만
        and session_start <= current_timestamp()
)

select * from transformed
