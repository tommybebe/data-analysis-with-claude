-- tests/assert_dau_lte_mau.sql
-- 커스텀 데이터 테스트: DAU ≤ MAU 무결성 검사
--
-- 비즈니스 규칙: 일간 활성 사용자(DAU)는 항상 월간 활성 사용자(MAU) 이하여야 함.
-- 위반 시 집계 로직 오류 또는 데이터 파이프라인 버그를 의미.
--
-- dbt test 실행: `dbt test --select assert_dau_lte_mau`
-- 이 쿼리가 행을 반환하면 테스트 실패 (dbt 커스텀 테스트 규약)

with dau_data as (
    -- 날짜·플랫폼별 DAU 집계
    select
        activity_date,
        platform,
        dau
    from {{ ref('fct_daily_active_users') }}
),

mau_data as (
    -- 월별·플랫폼별 MAU 집계
    select
        activity_month,
        platform,
        mau
    from {{ ref('fct_monthly_active_users') }}
),

-- DAU와 해당 월의 MAU 결합
joined as (
    select
        d.activity_date,
        d.platform,
        d.dau,
        m.mau,
        -- DAU가 MAU를 초과하면 위반 (이 행이 반환되면 테스트 실패)
        d.dau > m.mau as is_violation
    from dau_data d
    inner join mau_data m
        on date_trunc(d.activity_date, month) = m.activity_month
        and d.platform = m.platform
)

-- 위반 행만 반환 (행이 없으면 테스트 성공)
select
    activity_date,
    platform,
    dau,
    mau,
    dau - mau as dau_excess  -- 양수이면 DAU가 MAU 초과 → 버그
from joined
where is_violation
