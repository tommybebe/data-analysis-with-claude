-- tests/assert_retention_rate_bounded.sql
-- 커스텀 데이터 테스트: 리텐션 비율 범위 검사
--
-- 비즈니스 규칙:
--   1. retention_rate는 항상 0 이상 1 이하
--   2. weeks_since_signup = 0 (가입 주)의 retention_rate는 정확히 1.0
--   3. retained_users는 cohort_users를 초과할 수 없음
--
-- 위반 행이 반환되면 코호트 집계 로직 오류를 의미.

with cohort_data as (
    select
        cohort_week,
        cohort_users,
        weeks_since_signup,
        retained_users,
        retention_rate
    from {{ ref('fct_retention_cohort') }}
),

violations as (
    select
        cohort_week,
        cohort_users,
        weeks_since_signup,
        retained_users,
        retention_rate,

        -- 위반 유형 분류 (진단 목적)
        case
            when retention_rate < 0
                then 'retention_rate_negative'
            when retention_rate > 1
                then 'retention_rate_exceeds_one'
            when weeks_since_signup = 0 and abs(retention_rate - 1.0) > 0.0001
                then 'week0_not_100pct'
            when retained_users > cohort_users
                then 'retained_exceeds_cohort'
        end as violation_type

    from cohort_data
    where
        retention_rate < 0
        or retention_rate > 1
        or (weeks_since_signup = 0 and abs(retention_rate - 1.0) > 0.0001)
        or retained_users > cohort_users
)

-- 위반 행만 반환 (행이 없으면 테스트 성공)
select *
from violations
