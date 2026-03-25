-- stg_users.sql — Staging model for raw user profiles
-- Frozen snapshot from Module 0 output (prerequisite for Module 4)
-- Normalizes user data: type casting, default handling

with source as (
    select * from {{ source('raw', 'raw_users') }}
),

cleaned as (
    select
        cast(user_id as string) as user_id,
        cast(created_at as timestamp) as created_at,
        date(created_at) as signup_date,
        coalesce(cast(country as string), 'unknown') as country,
        cast(platform as string) as platform,
        coalesce(cast(acquisition_source as string), 'organic') as acquisition_source
    from source
)

select * from cleaned
