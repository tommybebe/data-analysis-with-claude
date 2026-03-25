-- fct_monthly_active_users.sql — MAU aggregation
-- Frozen snapshot from Module 0 output (prerequisite for Module 3)
-- Grain: month × platform

with events as (
    select * from {{ ref('stg_events') }}
),

monthly_active as (
    select
        date_trunc(event_date, month) as activity_month,
        platform,
        count(distinct user_id) as mau
    from events
    group by date_trunc(event_date, month), platform
)

select
    activity_month,
    platform,
    mau,
    current_timestamp() as updated_at
from monthly_active
