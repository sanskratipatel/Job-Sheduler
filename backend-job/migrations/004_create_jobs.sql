-- CREATE TABLE IF NOT EXISTS jobs (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

--     schedule_id UUID
--         REFERENCES job_schedules(id)
--         ON DELETE SET NULL,

--     name VARCHAR(255) NOT NULL,

--     job_type_id SMALLINT NOT NULL
--         REFERENCES job_types(id),

--     status_id SMALLINT NOT NULL
--         REFERENCES job_statuses(id),

--     payload JSONB NOT NULL DEFAULT '{}'::jsonb,

--     priority SMALLINT NOT NULL DEFAULT 0,

--     scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     attempt_count INTEGER NOT NULL DEFAULT 0,

--     max_attempts INTEGER NOT NULL DEFAULT 3,

--     timeout_seconds INTEGER NOT NULL DEFAULT 300,

--     idempotency_key VARCHAR(255),

--     payload_hash CHAR(64),

--     locked_by UUID
--         REFERENCES workers(id)
--         ON DELETE SET NULL,

--     locked_at TIMESTAMPTZ,

--     lease_expires_at TIMESTAMPTZ,

--     last_error TEXT,

--     started_at TIMESTAMPTZ,

--     completed_at TIMESTAMPTZ,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT jobs_attempt_count_valid
--         CHECK (
--             attempt_count >= 0
--         ),

--     CONSTRAINT jobs_max_attempts_valid
--         CHECK (
--             max_attempts BETWEEN 1 AND 20
--         ),

--     CONSTRAINT jobs_timeout_positive
--         CHECK (
--             timeout_seconds > 0
--         ),

--     CONSTRAINT jobs_priority_valid
--         CHECK (
--             priority BETWEEN -32768 AND 32767
--         )
-- ); 

BEGIN;

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    schedule_id UUID
        REFERENCES job_schedules(id),

    scheduled_for TIMESTAMPTZ,

    name VARCHAR(255) NOT NULL,

    job_type VARCHAR(100) NOT NULL
        REFERENCES job_types(code),

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    priority SMALLINT NOT NULL DEFAULT 0,

    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    attempt_count INTEGER NOT NULL DEFAULT 0,

    max_attempts INTEGER NOT NULL DEFAULT 3,

    timeout_seconds INTEGER NOT NULL DEFAULT 300,

    idempotency_key VARCHAR(255),

    payload_hash CHAR(64),

    locked_by UUID
        REFERENCES workers(id),

    locked_at TIMESTAMPTZ,

    lease_expires_at TIMESTAMPTZ,

    last_error TEXT,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT jobs_status_valid
        CHECK (
            status IN (
                'PENDING',
                'PROCESSING',
                'SUCCEEDED',
                'FAILED',
                'CANCELLED'
            )
        ),

    CONSTRAINT jobs_attempt_count_valid
        CHECK (
            attempt_count >= 0
            AND attempt_count <= max_attempts
        ),

    CONSTRAINT jobs_max_attempts_valid
        CHECK (
            max_attempts BETWEEN 1 AND 20
        ),

    CONSTRAINT jobs_timeout_positive
        CHECK (
            timeout_seconds > 0
        ),

    CONSTRAINT jobs_processing_has_owner
        CHECK (
            (status = 'PROCESSING')
            =
            (locked_by IS NOT NULL)
        ),

    CONSTRAINT jobs_lock_fields_together
        CHECK (
            (locked_by IS NULL) = (locked_at IS NULL)
            AND
            (locked_by IS NULL) = (lease_expires_at IS NULL)
        ),

    CONSTRAINT jobs_terminal_has_completed_at
        CHECK (
            (
                status IN (
                    'SUCCEEDED',
                    'FAILED',
                    'CANCELLED'
                )
            )
            =
            (completed_at IS NOT NULL)
        ),

    CONSTRAINT jobs_schedule_fields_together
        CHECK (
            (schedule_id IS NULL)
            =
            (scheduled_for IS NULL)
        )
);

COMMIT;