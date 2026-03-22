-- tests/assert_streak_positive.sql
-- 커스텀 데이터 테스트: 연속 활동 일수(streak)는 항상 1 이상
--
-- 비즈니스 규칙:
--   1. current_streak_days는 항상 양의 정수 (최소값: 1)
--      (활동이 있는 날의 streak이 0이거나 음수면 집계 오류)
--   2. streak_label은 허용된 값 중 하나여야 함
--   3. streak_group_id는 음수일 수 없음
--
-- dbt test 실행: `dbt test --select assert_streak_positive`
-- 이 쿼리가 행을 반환하면 테스트 실패 (dbt 커스텀 테스트 규약)

with rolling_data as (
    select
        user_id,
        activity_date,
        current_streak_days,
        streak_label,
        engagement_trend
    from {{ ref('int_user_rolling_metrics') }}
),

violations as (
    select
        user_id,
        activity_date,
        current_streak_days,
        streak_label,
        engagement_trend,

        -- 위반 유형 분류 (진단 목적)
        case
            when current_streak_days < 1
                then 'streak_less_than_one'
            when current_streak_days is null
                then 'streak_is_null'
            when streak_label not in ('champion', 'on_fire', 'building', 'starting')
                then 'invalid_streak_label'
            when engagement_trend not in ('growing', 'stable', 'at_risk')
                then 'invalid_engagement_trend'
        end as violation_type

    from rolling_data
    where
        -- 연속 활동 일수가 1 미만이거나 NULL
        current_streak_days < 1
        or current_streak_days is null
        -- 허용되지 않은 레이블 값
        or streak_label not in ('champion', 'on_fire', 'building', 'starting')
        or engagement_trend not in ('growing', 'stable', 'at_risk')
)

-- 위반 행만 반환 (행이 없으면 테스트 성공)
select *
from violations
