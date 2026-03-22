-- analyses/01_dau_trend_exploration.sql
-- DAU 트렌드 탐색 분석
--
-- ────────────────────────────────────────────────────────────────────────
-- dbt analyses 디렉토리란?
-- ────────────────────────────────────────────────────────────────────────
-- analyses/는 모델(models/)과 달리 구체화(materialization)되지 않는
-- 탐색적 SQL 파일을 보관하는 곳입니다.
--
-- 용도:
--   - 일회성 탐색 쿼리 (ad-hoc analysis)
--   - 복잡한 분석 패턴의 프로토타이핑
--   - `dbt compile` 후 BigQuery에서 직접 실행
--   - Claude에게 "이 패턴으로 분석해줘" 라고 지시하는 참고 코드
--
-- 실행 방법:
--   dbt compile --select 01_dau_trend_exploration
--   # 컴파일된 SQL: target/compiled/mobile_analytics/analyses/01_dau_trend_exploration.sql
--   # 컴파일된 파일을 BigQuery 콘솔에서 실행하거나 Python에서 읽어 사용

-- ════════════════════════════════════════════════════════════════════════
-- 분석 1: DAU 7일 이동 평균 (Moving Average)
-- ════════════════════════════════════════════════════════════════════════
-- 목적: 일별 노이즈를 제거하고 DAU 추세선 파악
-- 윈도우 함수: OVER (ORDER BY ... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)

with dau_base as (
    -- 플랫폼 합산 DAU (iOS + Android 합계)
    select
        activity_date,
        sum(dau) as total_dau,
        sum(new_users) as total_new_users,
        sum(total_revenue) as total_revenue_krw

    from {{ ref('fct_daily_active_users') }}
    group by activity_date
),

dau_with_trend as (
    select
        activity_date,
        total_dau,
        total_new_users,
        total_revenue_krw,

        -- 7일 이동 평균 (주간 사이클 노이즈 제거)
        -- ROWS BETWEEN 6 PRECEDING AND CURRENT ROW: 오늘 포함 7일
        avg(total_dau) over (
            order by activity_date
            rows between 6 preceding and current row
        )                                               as dau_7d_avg,

        -- 30일 이동 평균 (월간 트렌드 파악)
        avg(total_dau) over (
            order by activity_date
            rows between 29 preceding and current row
        )                                               as dau_30d_avg,

        -- 전일 대비 DAU 변화량
        total_dau - lag(total_dau) over (order by activity_date)
                                                        as dau_day_over_day,

        -- 전일 대비 변화율 (%)
        safe_divide(
            total_dau - lag(total_dau) over (order by activity_date),
            lag(total_dau) over (order by activity_date)
        ) * 100                                         as dau_dod_pct,

        -- 전주 동일 요일 대비 변화율 (요일 효과 제거)
        -- ROWS BETWEEN 7 PRECEDING AND 7 PRECEDING: 정확히 7일 전
        safe_divide(
            total_dau - lag(total_dau, 7) over (order by activity_date),
            lag(total_dau, 7) over (order by activity_date)
        ) * 100                                         as dau_wow_pct

    from dau_base
)

select
    activity_date,

    -- 원시 지표
    total_dau,
    total_new_users,
    round(total_revenue_krw, 0)                         as total_revenue_krw,

    -- 트렌드 지표 (소수점 반올림)
    round(dau_7d_avg, 0)                                as dau_7d_avg,
    round(dau_30d_avg, 0)                               as dau_30d_avg,

    -- 변화율
    dau_day_over_day,
    round(dau_dod_pct, 2)                               as dau_dod_pct,
    round(dau_wow_pct, 2)                               as dau_wow_pct,

    -- 요일 컬럼 (주간 패턴 분석용)
    format_date('%A', activity_date)                    as day_of_week,
    extract(dayofweek from activity_date)               as day_of_week_num  -- 1=일요일, 7=토요일

from dau_with_trend
order by activity_date


-- ════════════════════════════════════════════════════════════════════════
-- 분석 2: DAU/MAU stickiness 추세 (별도 실행)
-- ════════════════════════════════════════════════════════════════════════
-- 목적: 월별 stickiness 변화로 앱 의존도(habit formation) 추적
-- stickiness = avg(DAU) / MAU, 범위 0~1
-- 업계 기준: 20% 미만 = 낮음, 20~40% = 보통, 40%+ = 높음 (Facebook 수준)

/*
select
    m.activity_month,
    m.platform,
    m.mau,
    m.avg_dau,
    m.stickiness,

    -- stickiness 분류 라벨
    case
        when m.stickiness >= 0.40 then '높음 (40%+)'
        when m.stickiness >= 0.20 then '보통 (20-40%)'
        else '낮음 (20% 미만)'
    end                                                 as stickiness_label,

    -- 전월 대비 stickiness 변화
    m.stickiness - lag(m.stickiness) over (
        partition by m.platform
        order by m.activity_month
    )                                                   as stickiness_mom_change

from {{ ref('fct_monthly_active_users') }} m
order by m.activity_month, m.platform
*/


-- ════════════════════════════════════════════════════════════════════════
-- 분석 3: 플랫폼별 DAU 비율 추세 (별도 실행)
-- ════════════════════════════════════════════════════════════════════════
-- 목적: iOS vs Android DAU 비율 변화로 플랫폼 전략 모니터링

/*
with platform_daily as (
    select
        activity_date,
        platform,
        dau,
        -- 해당 날짜의 전체 DAU (플랫폼 합산)
        sum(dau) over (partition by activity_date)       as total_dau
    from {{ ref('fct_daily_active_users') }}
)

select
    activity_date,
    platform,
    dau,
    total_dau,
    -- 플랫폼 비율 (소수점 4자리)
    round(safe_divide(dau, total_dau), 4)               as platform_share,

    -- 7일 이동 평균 플랫폼 비율
    round(
        avg(safe_divide(dau, total_dau)) over (
            partition by platform
            order by activity_date
            rows between 6 preceding and current row
        ),
        4
    )                                                   as platform_share_7d_avg

from platform_daily
order by activity_date, platform
*/
