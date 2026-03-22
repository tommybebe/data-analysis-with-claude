-- stg_events.sql
-- 이벤트 로그 스테이징 모델
-- 원시 이벤트 데이터를 클렌징하고 타임존을 KST로 통일

{{ config(
    materialized='view',
    description='클렌징된 앱 이벤트 로그. UTC → KST 변환, 유효성 필터링 적용.'
) }}

with source as (
    select * from {{ source('mobile_app_raw', 'raw_events') }}
),

-- 비정상 레코드 필터링: NULL user_id 또는 미래 시점 이벤트 제거
filtered as (
    select *
    from source
    where
        user_id is not null
        and event_timestamp <= current_timestamp()
        and event_type is not null
),

-- 타임존 변환 및 날짜 파생 컬럼 생성
transformed as (
    select
        event_id,
        event_timestamp,
        -- KST(UTC+9) 변환 — 한국 시간 기준 DAU/MAU 집계에 사용
        timestamp(datetime(event_timestamp, 'Asia/Seoul')) as event_timestamp_kst,
        date(datetime(event_timestamp, 'Asia/Seoul')) as event_date_kst,

        user_id,
        session_id,
        event_type,

        -- JSON 속성 파싱 (이벤트 유형별 주요 필드 추출)
        json_extract_scalar(event_properties, '$.screen_name') as screen_name,
        json_extract_scalar(event_properties, '$.workout_type') as workout_type,
        json_extract_scalar(event_properties, '$.item_name') as item_name,
        safe_cast(
            json_extract_scalar(event_properties, '$.price_krw') as int64
        ) as price_krw,

        platform,
        app_version,
        device_model,

        -- 메타 컬럼
        _loaded_at
    from filtered
)

select * from transformed
