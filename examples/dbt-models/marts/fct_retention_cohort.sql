-- fct_retention_cohort.sql
-- 코호트 리텐션 마트 모델 (보너스)
-- 가입 주차(cohort) 기준 N일 후 잔존율 계산

{{ config(
    materialized='table',
    description='코호트 리텐션. 가입 주 기준 week-N 잔존율 계산. DAU/MAU와 함께 사용자 이탈 패턴 분석.'
) }}

with user_cohort as (
    -- 사용자별 코호트(가입 주) 결정
    select
        user_id,
        signup_date_kst,
        date_trunc(signup_date_kst, week(monday)) as cohort_week
    from {{ ref('stg_users') }}
    where signup_date_kst is not null
),

user_activity as (
    -- 사용자별 활동 날짜 목록
    select distinct
        user_id,
        event_date_kst as activity_date
    from {{ ref('stg_events') }}
),

-- 코호트별 N주차 활동 여부
cohort_activity as (
    select
        c.cohort_week,
        c.user_id,
        a.activity_date,
        -- 가입 주 기준 몇 주차에 활동했는지
        date_diff(a.activity_date, c.cohort_week, week(monday)) as weeks_since_signup
    from user_cohort c
    inner join user_activity a
        on c.user_id = a.user_id
    where
        a.activity_date >= c.cohort_week
        -- 최대 12주까지 추적
        and date_diff(a.activity_date, c.cohort_week, week(monday)) <= 12
),

-- 코호트 크기 (가입 주별 사용자 수)
cohort_size as (
    select
        cohort_week,
        count(distinct user_id) as cohort_users
    from user_cohort
    group by 1
),

-- 주차별 잔존 사용자 수
retention as (
    select
        cohort_week,
        weeks_since_signup,
        count(distinct user_id) as retained_users
    from cohort_activity
    group by 1, 2
)

select
    r.cohort_week,
    s.cohort_users,
    r.weeks_since_signup,
    r.retained_users,
    -- 잔존율 (week-0은 항상 100%)
    round(safe_divide(r.retained_users, s.cohort_users), 4) as retention_rate
from retention r
inner join cohort_size s
    on r.cohort_week = s.cohort_week
order by r.cohort_week, r.weeks_since_signup
