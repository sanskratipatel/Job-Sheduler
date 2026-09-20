-- CREATE TABLE IF NOT EXISTS job_executions (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

--     job_id UUID NOT NULL
--         REFERENCES jobs(id)
--         ON DELETE CASCADE,

--     worker_id UUID
--         REFERENCES workers(id)
--         ON DELETE SET NULL,

--     attempt_number INTEGER NOT NULL,

--     status_id SMALLINT NOT NULL
--         REFERENCES execution_statuses(id),

--     started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     finished_at TIMESTAMPTZ,

--     duration_ms BIGINT,

--     error_message TEXT,

--     error_traceback TEXT,

--     output JSONB,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT job_executions_attempt_positive
--         CHECK (
--             attempt_number > 0
--         ),

--     CONSTRAINT job_executions_duration_positive
--         CHECK (
--             duration_ms IS NULL
--             OR duration_ms >= 0
--         ),

--     CONSTRAINT job_executions_unique_attempt
--         UNIQUE (
--             job_id,
--             attempt_number
--         )
-- ); 

BEGIN;

CREATE TABLE IF NOT EXISTS job_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    job_id UUID NOT NULL
        REFERENCES jobs(id)
        ON DELETE CASCADE,

    worker_id UUID
        REFERENCES workers(id),

    attempt_number INTEGER NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    finished_at TIMESTAMPTZ,

    duration_ms BIGINT,

    error_message TEXT,

    error_traceback TEXT,

    output JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT job_executions_status_valid
        CHECK (
            status IN (
                'RUNNING',
                'SUCCEEDED',
                'FAILED',
                'TIMED_OUT',
                'ABANDONED'
            )
        ),

    CONSTRAINT job_executions_attempt_positive
        CHECK (
            attempt_number > 0
        ),

    CONSTRAINT job_executions_duration_valid
        CHECK (
            duration_ms IS NULL
            OR duration_ms >= 0
        ),

    CONSTRAINT job_executions_finished_when_not_running
        CHECK (
            (status = 'RUNNING')
            =
            (finished_at IS NULL)
        ),

    CONSTRAINT job_executions_unique_attempt
        UNIQUE (job_id, attempt_number)
);

COMMIT;