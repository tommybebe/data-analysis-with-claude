-- stg_users.sql
-- 사용자 프로필 스테이징 모델
-- 사용자 정보를 정규화하고 파생 컬럼 생성

{{ config(
    materialized='view',
    description='정규화된 사용자 프로필. 가입 일자 KST 변환, 가입 경과일 계산.'
) }}

with source as (
    select * from {{ source('mobile_app_raw', 'raw_users') }}
),

transformed as (
    select
        user_id,

        -- 가입 시각 KST 변환
        signup_timestamp,
        date(datetime(signup_timestamp, 'Asia/Seoul')) as signup_date_kst,

        -- 가입 후 경과일 (리텐션 분석 기반 데이터)
        date_diff(
            current_date('Asia/Seoul'),
            date(datetime(signup_timestamp, 'Asia/Seoul')),
            day
        ) as days_since_signup,

        country,
        language,
        platform,
        device_type,
        initial_app_version,
        subscription_tier,
        age_group,
        referral_source,
        is_active,
        last_active_date,

        _loaded_at
    from source
    where user_id is not null
)

select * from transformed
