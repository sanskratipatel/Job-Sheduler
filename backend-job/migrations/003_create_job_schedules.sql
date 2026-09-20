-- CREATE TABLE IF NOT EXISTS job_schedules (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

--     name VARCHAR(255) NOT NULL,

--     job_type_id SMALLINT NOT NULL
--         REFERENCES job_types(id),

--     payload JSONB NOT NULL DEFAULT '{}'::jsonb,

--     schedule_type VARCHAR(50) NOT NULL,

--     cron_expression VARCHAR(100),

--     timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',

--     next_run_at TIMESTAMPTZ,

--     is_active BOOLEAN NOT NULL DEFAULT TRUE,

--     max_attempts INTEGER NOT NULL DEFAULT 3,

--     timeout_seconds INTEGER NOT NULL DEFAULT 300,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT job_schedules_schedule_type_valid
--         CHECK (
--             schedule_type IN (
--                 'ONCE',
--                 'CRON'
--             )
--         ),

--     CONSTRAINT job_schedules_max_attempts_valid
--         CHECK (
--             max_attempts BETWEEN 1 AND 20
--         ),

--     CONSTRAINT job_schedules_timeout_positive
--         CHECK (
--             timeout_seconds > 0
--         ),

--     CONSTRAINT job_schedules_cron_required
--         CHECK (
--             schedule_type = 'ONCE'
--             OR cron_expression IS NOT NULL
--         )
-- ); 

BEGIN;

CREATE TABLE IF NOT EXISTS job_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,
    description TEXT,

    job_type VARCHAR(100) NOT NULL
        REFERENCES job_types(code),

    payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    priority SMALLINT NOT NULL DEFAULT 0,

    max_attempts INTEGER NOT NULL DEFAULT 3,

    timeout_seconds INTEGER NOT NULL DEFAULT 300,

    schedule_type VARCHAR(20) NOT NULL,

    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',

    run_at TIMESTAMPTZ,

    run_time TIME,

    interval_count SMALLINT NOT NULL DEFAULT 1,

    days_of_week SMALLINT[],

    day_of_month SMALLINT,

    month_of_year SMALLINT,

    run_dates DATE[],

    cron_expression VARCHAR(100),

    start_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    end_at TIMESTAMPTZ,

    max_runs INTEGER,

    misfire_policy VARCHAR(20) NOT NULL DEFAULT 'RUN_ONCE',

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    next_run_at TIMESTAMPTZ,

    last_run_at TIMESTAMPTZ,

    run_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT job_schedules_type_valid
        CHECK (
            schedule_type IN (
                'ONCE',
                'DAILY',
                'WEEKLY',
                'MONTHLY',
                'YEARLY',
                'SPECIFIC_DATES',
                'CRON'
            )
        ),

    CONSTRAINT job_schedules_status_valid
        CHECK (
            status IN (
                'ACTIVE',
                'PAUSED',
                'COMPLETED',
                'ARCHIVED'
            )
        ),

    CONSTRAINT job_schedules_misfire_valid
        CHECK (
            misfire_policy IN (
                'SKIP',
                'RUN_ONCE'
            )
        ),

    CONSTRAINT job_schedules_max_attempts_valid
        CHECK (max_attempts BETWEEN 1 AND 20),

    CONSTRAINT job_schedules_timeout_positive
        CHECK (timeout_seconds > 0),

    CONSTRAINT job_schedules_interval_positive
        CHECK (interval_count >= 1),

    CONSTRAINT job_schedules_days_of_week_valid
        CHECK (
            days_of_week <@
            ARRAY[1, 2, 3, 4, 5, 6, 7]::SMALLINT[]
        ),

    CONSTRAINT job_schedules_day_of_month_valid
        CHECK (
            day_of_month BETWEEN 1 AND 31
            OR day_of_month = -1
        ),

    CONSTRAINT job_schedules_month_of_year_valid
        CHECK (
            month_of_year BETWEEN 1 AND 12
        ),

    CONSTRAINT job_schedules_window_valid
        CHECK (
            end_at IS NULL
            OR end_at > start_at
        ),

    CONSTRAINT job_schedules_max_runs_positive
        CHECK (
            max_runs IS NULL
            OR max_runs > 0
        ),

    CONSTRAINT job_schedules_run_count_valid
        CHECK (run_count >= 0),

    CONSTRAINT job_schedules_once_needs_run_at
        CHECK (
            schedule_type <> 'ONCE'
            OR run_at IS NOT NULL
        ),

    CONSTRAINT job_schedules_cron_needs_expression
        CHECK (
            schedule_type <> 'CRON'
            OR cron_expression IS NOT NULL
        ),

    CONSTRAINT job_schedules_calendar_needs_run_time
        CHECK (
            schedule_type NOT IN (
                'DAILY',
                'WEEKLY',
                'MONTHLY',
                'YEARLY',
                'SPECIFIC_DATES'
            )
            OR run_time IS NOT NULL
        ),

    CONSTRAINT job_schedules_weekly_needs_days
        CHECK (
            schedule_type <> 'WEEKLY'
            OR COALESCE(cardinality(days_of_week), 0) >= 1
        ),

    CONSTRAINT job_schedules_monthly_needs_day
        CHECK (
            schedule_type NOT IN ('MONTHLY', 'YEARLY')
            OR day_of_month IS NOT NULL
        ),

    CONSTRAINT job_schedules_yearly_needs_month
        CHECK (
            schedule_type <> 'YEARLY'
            OR month_of_year IS NOT NULL
        ),

    CONSTRAINT job_schedules_dates_needs_list
        CHECK (
            schedule_type <> 'SPECIFIC_DATES'
            OR COALESCE(cardinality(run_dates), 0) >= 1
        ),

    CONSTRAINT job_schedules_active_needs_next_run
        CHECK (
            status <> 'ACTIVE'
            OR next_run_at IS NOT NULL
        )
);

COMMIT;