-- stg_events.sql — Staging model for raw app events
-- Frozen snapshot from Module 0 output (prerequisite for Module 1)
-- Cleanses raw events: type casting, timezone normalization, deduplication

with source as (
    select * from {{ source('raw', 'raw_events') }}
),

deduplicated as (
    select
        *,
        row_number() over (partition by event_id order by event_timestamp) as _row_num
    from source
),

cleaned as (
    select
        cast(event_id as string) as event_id,
        cast(user_id as string) as user_id,
        cast(event_type as string) as event_type,
        cast(event_timestamp as timestamp) as event_timestamp,
        date(event_timestamp) as event_date,
        cast(platform as string) as platform,
        cast(app_version as string) as app_version,
        cast(properties as string) as properties
    from deduplicated
    where _row_num = 1
)

select * from cleaned
