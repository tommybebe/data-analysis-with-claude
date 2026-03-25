-- fct_retention_cohort.sql — Cohort retention analysis
-- Frozen snapshot from Module 0 output (prerequisite for Module 1)
-- Grain: cohort_month × months_since_signup

with users as (
    select * from {{ ref('stg_users') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

user_cohorts as (
    select
        user_id,
        date_trunc(signup_date, month) as cohort_month
    from users
),

user_activity as (
    select
        e.user_id,
        uc.cohort_month,
        date_trunc(e.event_date, month) as activity_month
    from events e
    inner join user_cohorts uc on e.user_id = uc.user_id
    group by e.user_id, uc.cohort_month, date_trunc(e.event_date, month)
),

retention as (
    select
        cohort_month,
        date_diff(activity_month, cohort_month, month) as months_since_signup,
        count(distinct user_id) as retained_users
    from user_activity
    group by cohort_month, date_diff(activity_month, cohort_month, month)
),

cohort_sizes as (
    select
        cohort_month,
        count(distinct user_id) as cohort_size
    from user_cohorts
    group by cohort_month
)

select
    r.cohort_month,
    r.months_since_signup,
    r.retained_users,
    cs.cohort_size,
    round(safe_divide(r.retained_users, cs.cohort_size) * 100, 2) as retention_rate,
    current_timestamp() as updated_at
from retention r
inner join cohort_sizes cs on r.cohort_month = cs.cohort_month
