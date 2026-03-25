-- fct_daily_active_users.sql — DAU aggregation
-- Frozen snapshot from Module 0 output (prerequisite for Module 2)
-- Grain: date × platform

with events as (
    select * from {{ ref('stg_events') }}
),

daily_active as (
    select
        event_date,
        platform,
        count(distinct user_id) as dau
    from events
    group by event_date, platform
)

select
    event_date,
    platform,
    dau,
    current_timestamp() as updated_at
from daily_active
