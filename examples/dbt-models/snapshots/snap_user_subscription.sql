-- snapshots/snap_user_subscription.sql
-- 사용자 구독 등급 변경 이력 스냅샷 (SCD Type 2)
--
-- ────────────────────────────────────────────────────────────────────────
-- 스냅샷(Snapshot) 패턴이란?
-- ────────────────────────────────────────────────────────────────────────
-- 원시 테이블(raw_users)은 현재 상태만 저장합니다. 예를 들어 사용자가
-- free → premium으로 업그레이드하면 subscription_tier 값만 변경되고
-- 이전 이력은 사라집니다.
--
-- dbt Snapshot은 "천천히 변하는 차원(SCD, Slowly Changing Dimension)"을
-- Type 2 방식으로 추적합니다:
--   - 변경이 발생할 때마다 새 행을 추가 (기존 행은 dbt_valid_to로 닫힘)
--   - 유효 기간(dbt_valid_from ~ dbt_valid_to)으로 이력 조회 가능
--   - 현재 상태: dbt_valid_to IS NULL 인 행
--
-- 활용 예시:
--   - "3개월 전 free 사용자 중 현재 premium으로 전환된 비율은?" (업그레이드 분석)
--   - "구독 등급이 여러 번 변경된 사용자의 평균 LTV는?" (행동 변화 분석)
--   - "특정 마케팅 캠페인 이후 premium 전환율이 증가했는가?" (캠페인 효과 측정)
--
-- BigQuery 비용 최적화:
--   - 스냅샷 테이블은 TABLE로 구체화 (VIEW 사용 불가)
--   - 이력 테이블은 크기가 커질 수 있으므로 파티션 적용 권장
--   - `dbt snapshot` 명령은 변경분만 처리하여 전체 재처리 비용 방지
--
-- 실행 방법:
--   dbt snapshot
--   dbt snapshot --select snap_user_subscription

{% snapshot snap_user_subscription %}

{{
    config(
        -- 스냅샷 대상 스키마 (dbt_project.yml의 snapshots.+target_schema 참조)
        target_schema='snapshots',

        -- 변경 감지 전략: 'timestamp' 또는 'check'
        -- 'timestamp': updated_at 컬럼 기준 변경 감지 (권장, 성능 우수)
        -- 'check': 지정한 컬럼 값을 직접 비교 (updated_at 없을 때 사용)
        strategy='check',

        -- check 전략: 이 컬럼들의 값이 변경되면 새 이력 행 추가
        -- subscription_tier: 구독 등급 변경 추적
        -- is_active: 활성/비활성 상태 변경 추적
        check_cols=['subscription_tier', 'is_active'],

        -- 고유 키: 각 레코드를 식별하는 기본 키 컬럼
        unique_key='user_id',

        -- 타임스탬프 기준: dbt가 스냅샷 시점을 기록하는 컬럼
        -- dbt가 자동으로 dbt_valid_from, dbt_valid_to를 관리
        invalidate_hard_deletes=true
    )
}}

-- 스냅샷 소스 쿼리 (raw_users에서 직접 읽음)
-- 주의: 스냅샷은 staging이 아닌 raw 테이블을 직접 읽는 것이 일반적
-- (staging은 VIEW이므로 check 전략의 중간 변환이 감지 오류를 유발할 수 있음)
select
    user_id,
    subscription_tier,
    is_active,
    last_active_date,

    -- 참고 컬럼: 스냅샷 맥락 파악용
    country,
    platform,
    referral_source,

    -- 가입일 (코호트 분석과의 조인 키)
    signup_date,

    -- 데이터 적재 시각 (스냅샷 소스 추적용)
    _loaded_at

from {{ source('mobile_app_raw', 'raw_users') }}

-- 유효한 사용자만 추적 (NULL user_id 제외)
where user_id is not null

{% endsnapshot %}

-- ────────────────────────────────────────────────────────────────────────
-- 스냅샷 실행 후 생성되는 컬럼 (dbt가 자동 추가)
-- ────────────────────────────────────────────────────────────────────────
-- dbt_scd_id       : 스냅샷 행 고유 식별자 (user_id + dbt_updated_at 해시)
-- dbt_updated_at   : 이 스냅샷 행이 생성/업데이트된 시각
-- dbt_valid_from   : 이 상태가 유효해진 시각 (이전 행의 dbt_valid_to)
-- dbt_valid_to     : 이 상태가 끝난 시각 (NULL이면 현재 유효한 상태)
--
-- 활용 쿼리 예시:
-- ─────────────────────────────────────────────────────────────────────
-- -- 현재 구독 등급 조회 (최신 상태)
-- SELECT user_id, subscription_tier
-- FROM snap_user_subscription
-- WHERE dbt_valid_to IS NULL;
--
-- -- 지난 6개월 내 premium으로 업그레이드한 사용자
-- SELECT user_id,
--        dbt_valid_from AS upgrade_date,
--        subscription_tier AS new_tier
-- FROM snap_user_subscription
-- WHERE subscription_tier IN ('premium', 'premium_plus')
--   AND dbt_valid_from >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH);
--
-- -- 구독 등급 변경 횟수가 가장 많은 사용자 TOP 10
-- SELECT user_id,
--        COUNT(*) - 1 AS tier_changes  -- 최초 행 제외
-- FROM snap_user_subscription
-- GROUP BY user_id
-- HAVING tier_changes > 0
-- ORDER BY tier_changes DESC
-- LIMIT 10;
